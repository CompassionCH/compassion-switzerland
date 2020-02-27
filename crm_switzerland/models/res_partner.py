##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def schedule_meeting(self):
        old_action = super().schedule_meeting()
        new_action = self.env.ref(
            "crm_switzerland.action_calendar_event_partner"
        ).read()[0]
        new_action["domain"] = [("partner_ids", "in", self.ids)]
        new_action["context"] = {
            "default_partner_ids": old_action["context"]["default_partner_ids"]
        }
        return new_action

    @api.model
    def _notify_prepare_template_context(self, message):
        # modification of context for lang
        message = message.with_context(lang=self[:1].lang or self.env.lang)
        return super()._notify_prepare_template_context(message)
