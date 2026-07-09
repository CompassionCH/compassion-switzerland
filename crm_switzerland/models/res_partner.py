from odoo import _, models

CHURCH_ENGAGEMENT_DEPARTMENT = "Church Engagement"


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        if "email" in vals:
            # Propagate the email change to the related crm.lead
            for partner in self:
                opportunities = self.env["crm.lead"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("email_from", "=", partner.email),
                    ]
                )
                opportunities.write({"email_from": vals["email"]})
        if "user_id" in vals:
            # Propagate the salesperson change to the related crm.lead of
            # churches (simple push, no candidate arbitration: an explicit
            # edit on the church itself is already a deliberate decision).
            for partner in self.filtered("is_church"):
                opportunities = self.env["crm.lead"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("user_id", "=", partner.user_id.id),
                    ]
                )
                opportunities.write({"user_id": vals["user_id"]})
        super().write(vals)
        return True

    def _church_salesperson_employee(self, user):
        if not user:
            return self.env["hr.employee"]
        return (
            self.env["hr.employee"]
            .with_context(active_test=False)
            .search([("user_id", "=", user.id)], limit=1)
        )

    def _is_church_salesperson_valid(self, user):
        """A salesperson is invalid only if they have an archived
        hr.employee record. No employee record at all still counts as
        valid (nothing marks them as archived)."""
        if not user:
            return False
        employee = self._church_salesperson_employee(user)
        return not (employee and not employee.active)

    def _is_church_engagement(self, user):
        employee = self._church_salesperson_employee(user)
        return bool(
            employee and employee.department_id.name == CHURCH_ENGAGEMENT_DEPARTMENT
        )

    def resolve_church_salesperson(self, candidate):
        """Decide the church's salesperson given a candidate coming from one
        of its opportunities.

        :param candidate: res.users candidate proposed as salesperson
        :return: (new_user_id or False, notify_daniel: bool)
                 new_user_id is False when nothing should change.
        """
        self.ensure_one()
        current = self.user_id
        candidate_valid = self._is_church_salesperson_valid(candidate)
        current_valid = self._is_church_salesperson_valid(current)

        if not candidate_valid:
            if not current_valid:
                # No valid candidate at all (current may be empty or
                # archived, and the incoming candidate is invalid too).
                return False, True
            return False, False

        if not current or not current_valid:
            return candidate, False

        # Both current and candidate are valid: prefer whoever is in the
        # Church Engagement department; if both/neither are, keep the
        # lowest user id (deterministic tiebreak).
        candidate_in_dept = self._is_church_engagement(candidate)
        current_in_dept = self._is_church_engagement(current)
        if current_in_dept and not candidate_in_dept:
            return False, False
        if candidate_in_dept and not current_in_dept:
            return candidate, False
        if current.id <= candidate.id:
            return False, False
        return candidate, False

    def sync_salesperson_from_lead(self, candidate_user_id, lead_id):
        """Job target for the async church/lead salesperson sync (see
        crm.lead._sync_church_salesperson, which enqueues this via
        with_delay_sh instead of calling it inline)."""
        self.ensure_one()
        candidate = self.env["res.users"].browse(candidate_user_id)
        new_salesperson, notify = self.resolve_church_salesperson(candidate)
        if new_salesperson:
            self.write({"user_id": new_salesperson.id})
        elif notify:
            lead = self.env["crm.lead"].browse(lead_id)
            self._notify_daniel_no_church_salesperson(
                context_note=_(
                    " (triggered by opportunity %(lead)s, salesperson %(user)s)"
                )
                % {"lead": lead.name, "user": candidate.name}
            )

    def _notify_daniel_no_church_salesperson(self, context_note=""):
        self.ensure_one()
        daniel = self.env["res.users"].search([("login", "=", "dmuller")], limit=1)
        if not daniel:
            return
        activity_type = self.env.ref("mail.mail_activity_data_todo")
        already_notified = self.activity_ids.filtered(
            lambda a: a.activity_type_id == activity_type and a.user_id == daniel
        )
        if already_notified:
            return
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Church without a valid Salesperson"),
            note=_(
                "No valid (non-archived) Salesperson could be determined "
                "automatically for this church. Please review and assign "
                "one manually.%(context_note)s"
            )
            % {"context_note": context_note},
            user_id=daniel.id,
        )
