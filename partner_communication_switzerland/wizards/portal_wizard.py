##############################################################################
#
#    Copyright (C) 2018-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class PortalWizard(models.TransientModel):
    _inherit = "portal.wizard"

    invitation_config_id = fields.Many2one(
        "partner.communication.config", readonly=False
    )


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    uid_communication_id = fields.Many2one("partner.communication.job", readonly=False)

    def action_grant_access(self):
        """Send our own invitation communication instead of the portal e-mail.

        The signup token is prepared by the super() call, which also disables
        the standard portal e-mail (see partner_compassion `_send_email`).
        """
        res = super().action_grant_access()

        if self.env.context.get("create_communication"):
            self.create_uid_communication()

        return res

    def create_uid_communication(self):
        """create a communication that contain a login url"""
        self.ensure_one()
        if not self.env.user.email:
            raise UserError(
                _(
                    "You must have an email address in"
                    " your User Preferences to send emails."
                )
            )

        # user_id only depends on partner_id, so it is not recomputed when
        # the user was just created by the portal access grant.
        self.invalidate_recordset(["user_id"])
        user = self.user_id

        self.uid_communication_id = self.env["partner.communication.job"].create(
            {
                "partner_id": user.partner_id.id,
                "object_ids": user.id,
                "config_id": self.wizard_id.invitation_config_id.id,
            }
        )
