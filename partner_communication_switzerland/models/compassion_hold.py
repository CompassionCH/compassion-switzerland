##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from odoo import api, fields, models


class CompassionHold(models.Model):
    """Send Communication when Hold Removal is received."""

    _inherit = "compassion.hold"

    no_money_extension_duration = fields.Integer(
        compute="_compute_no_money_extension_duration"
    )

    @api.multi
    def _compute_no_money_extension_duration(self):
        """
        Gets the default No Money hold extension duration
        :return: integer: hold duration in days
        """
        settings = self.env["res.config.settings"].sudo()
        for hold in self:
            if hold.no_money_extension < 2:
                hold.no_money_extension_duration = settings.get_param(
                    "no_money_hold_duration"
                )
            else:
                hold.no_money_extension_duration = settings.get_param(
                    "no_money_hold_extension"
                )

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        ids = super().beneficiary_hold_removal(commkit_data)
        now = datetime.now()
        # when unexpected exit of already assigned child
        # CO-3692 : if the hold was already expired and we wrongly receive
        #           another message from GMC child state won't be R (released)
        for hold in self.browse(ids).filtered(
            lambda h: h.expiration_date > now
            and h.child_id.sponsorship_ids
            and h.child_id.state == "R"
        ):
            sponsorship = hold.child_id.sponsorship_ids[:1]
            communication_type = self.env.ref(
                "partner_communication_switzerland.lifecycle_child_unplanned_exit"
            )
            sponsorship.send_communication(communication_type, both=True)

        return ids

    @api.multi
    def postpone_no_money_hold(self, additional_text=None):
        """
        Send a communication to sponsor for reminding the payment.
        TODO: Attach a payment slip
        :param additional_text: text to add in the notification to hold owner
        :return: None
        """
        failed = self.env[self._name]
        first_reminder_config = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_1"
        )
        second_reminder_config = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_2"
        )
        third_reminder_config = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_3"
        )

        # Check communications already pending and put them back to their state
        first_reminders = self.env["partner.communication.job"].search(
            [("config_id", "=", first_reminder_config.id), ("state", "=", "pending")]
        )
        if first_reminders:
            first_pending_holds = first_reminders.get_objects().mapped(
                "child_id.hold_id"
            )
            (first_pending_holds & self).write({"no_money_extension": 0})
        second_reminders = self.env["partner.communication.job"].search(
            [("config_id", "=", second_reminder_config.id), ("state", "=", "pending")]
        )
        if second_reminders:
            second_pending_holds = second_reminders.get_objects().mapped(
                "child_id.hold_id"
            )
            (second_pending_holds & self).write({"no_money_extension": 1})
        third_reminders = self.env["partner.communication.job"].search(
            [("config_id", "=", third_reminder_config.id), ("state", "=", "pending")]
        )
        if third_reminders:
            third_pending_holds = third_reminders.get_objects().mapped(
                "child_id.hold_id"
            )
            (third_pending_holds & self).write({"no_money_extension": 2})

        # Generate reminders while postponing the hold expiration
        failed += self.filtered(lambda h: h.no_money_extension > 1)._send_hold_reminder(
            third_reminder_config
        )
        failed += self.filtered(
            lambda h: h.no_money_extension == 1
        )._send_hold_reminder(second_reminder_config)
        failed += self.filtered(
            lambda h: h.no_money_extension == 0
        )._send_hold_reminder(first_reminder_config)

        if failed:
            # Send warning to Admin users
            child_codes = failed.mapped("child_id").read(["local_id"])
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            links = [
                f'<a href="{base_url}/web#id={data["id"]}&'
                f"view_type=form&model=compassion.child"
                f'&menu_id=442&action=581">{data["local_id"]}</a>'
                for data in child_codes
            ]
            hold_string = list()
            for i in range(0, len(failed)):
                hold_string.append(failed[i].hold_id + " (" + links[i] + " )")
            self.env["mail.mail"].create(
                {
                    "subject": "URGENT: Postpone no money holds failed!",
                    "author_id": self.env.user.partner_id.id,
                    "recipient_ids": [(6, 0, [18000, 13])],
                    "body_html": "These holds should be urgently verified: <br/>"
                    "<br/>" + ", ".join(hold_string),
                }
            ).send()

    def _send_hold_reminder(self, communication):
        """
        Sends the hold reminder communication to sponsors and postpone the
        hold.
        :param communication: the type of communication
        :return: recordset of failed updated holds.
        """
        notification_text = (
            "\n\nA reminder has been prepared for the " "sponsor {} ({})"
        )
        failed = self.env[self._name]
        for hold in self.with_context(
            default_auto_send=False,
            default_print_subject=False,
            default_print_header=True,
        ):
            sponsorship = hold.child_id.sponsorship_ids[:1]
            sponsor = hold.child_id.sponsor_id
            # Filter draft sponsorships and where we wait for
            # the bank authorization
            if sponsorship.state == "draft" or (
                sponsorship.state == "mandate" and sponsor.bank_ids
            ):
                try:
                    previous_extension = hold.no_money_extension
                    super(CompassionHold, hold).postpone_no_money_hold()
                    if previous_extension < hold.no_money_extension:
                        hold.no_money_extension = previous_extension
                    continue
                except:
                    failed += hold
                    continue
            try:
                super(CompassionHold, hold).postpone_no_money_hold(
                    notification_text.format(sponsor.name, sponsor.ref)
                )
                sponsorship.send_communication(communication, correspondent=False)
            except:
                failed += hold
        return failed
