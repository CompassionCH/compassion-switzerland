##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import _, fields, models
from odoo.exceptions import UserError


class ResPartnerCreatePortalWizard(models.TransientModel):
    """creation of a portal user wizard will send a email
    with the identifier if the user used the checkbox"""

    _name = "res.partner.create.portal.wizard"
    _description = "Take a partner and make it a odoo user"

    create_communication = fields.Boolean("Send an e-mail invitation", default=True)

    config_id = fields.Many2one(
        "partner.communication.config",
        "choose a communication",
        domain="[('model', '=', 'res.users')]",
        default=lambda self: self.env.ref(
            "partner_communication_switzerland.portal_welcome_config"
        ).id,
        readonly=False,
    )

    def button_create_portal_user(self):
        self.ensure_one()
        portal = self.env["portal.wizard"].create(
            {"invitation_config_id": self.config_id.id}
        )
        users_portal = portal.user_ids
        # granting an access twice raises an error in the standard wizard
        to_grant = users_portal.filtered(
            lambda u: not u.is_portal and not u.is_internal
        )

        # create a temporary fake email address for partner without email,
        # their accounts have to be activate manually
        no_mail = to_grant.filtered(lambda u: not u.email)
        unnamed = no_mail.filtered(
            lambda u: not u.partner_id.firstname or not u.partner_id.lastname
        )
        if unnamed:
            raise UserError(
                _(
                    "Please fill in the missing names, or set an e-mail "
                    "address, for: %s",
                    ", ".join(unnamed.mapped("partner_id.display_name")),
                )
            )
        for user in no_mail:
            partner = user.partner_id
            user.email = (
                partner.firstname[0].lower() + partner.lastname.lower() + "@cs.local"
            )

        # The standard wizard grants the access one partner at a time.
        for portal_user in to_grant:
            portal_user.action_grant_access()

        action = True
        if self.create_communication:
            # action_grant_access, skipped here, is what prepares the token
            (users_portal - to_grant).mapped("partner_id").sudo().signup_prepare()
            for portal_user in users_portal:
                portal_user.create_uid_communication()
            uid_communication = users_portal.mapped("uid_communication_id")
            action = {
                "name": _("Communications"),
                "type": "ir.actions.act_window",
                "res_model": "partner.communication.job",
                "view_type": "form",
                "view_mode": "list,form",
                "domain": [("id", "in", uid_communication.ids)],
            }

        # done last: the communications need the address still set
        no_mail.mapped("partner_id").write({"email": False})
        return action

    def button_cancel(self):
        return True
