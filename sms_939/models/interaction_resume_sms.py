##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api


class InteractionResume(models.TransientModel):
    _inherit = "interaction.resume"

    @api.model
    def populate_resume(self, partner_id):
        """
        Creates the rows for the resume of given partner
        :param partner_id: the partner
        :return: True
        """
        super().populate_resume(partner_id)
        self.env.cr.execute(f"""
              SELECT
                'SMS' as communication_type,
                sms.date as communication_date,
                sms.partner_id as partner_id,
                NULL as email,
                sms.subject as subject,
                sms.text as body,
                'out' as direction,
                0 as phone_id,
                0 as email_id,
                0 as message_id,
                0 as paper_id,
                NULL as tracking_status
                FROM "sms_log" as sms
                WHERE (sms.partner_id = {partner_id})
                """)
        for row in self.env.cr.dictfetchall():
            self.create(row)
        return True
