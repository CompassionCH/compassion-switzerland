##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_muskathlon = fields.Boolean(
        compute="_compute_is_muskathlon", help="tells if it's a Muskathlon participant")

    def _compute_is_muskathlon(self):
        type_muskathlon = self.env.ref("muskathlon.event_type_muskathlon")
        for partner in self:
            partner.is_muskathlon = type_muskathlon in partner.registration_ids.mapped(
                "compassion_event_id.event_type_id")

    @api.multi
    def agree_to_child_protection_charter(self):
        res = super(ResPartner, self).agree_to_child_protection_charter()
        task = self.env.ref("muskathlon.task_sign_child_protection")
        for partner in self:
            for registration in partner.registration_ids:
                if task in registration.incomplete_task_ids:
                    registration.write({"completed_task_ids": [(4, task.id)]})
        return res


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def signup(self, values, token=None):
        """ Mark acccount activation task done for Muskathlon participant. """
        res = super(ResUsers, self).signup(values, token)
        login = res[1]
        user = self.env["res.users"].search([("login", "=", login)])
        registration = user.partner_id.registration_ids[:1]
        if registration.event_id.event_type_id == self.env.ref(
                "muskathlon.event_type_muskathlon"
        ):
            registration.write(
                {
                    "completed_task_ids": [
                        (4, self.env.ref("muskathlon.task_activate_account").id)
                    ]
                }
            )
        return res
