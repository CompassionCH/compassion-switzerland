# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields


class PartnerCommunication(models.Model):
    _inherit = 'partner.communication.job'

    event_id = fields.Many2one('crm.event.compassion', 'Event')

    @api.multi
    def get_success_story(self):
        return "Success Story"

    @api.multi
    def open_related(self):
        """ Select a better view for invoice lines. """
        res = super(PartnerCommunication, self).open_related()
        if self.config_id.model == 'account.invoice.line':
            res['context'] = self.with_context(
                tree_view_ref='sponsorship_compassion'
                              '.view_invoice_line_partner_tree',
                group_by=False
            ).env.context
        return res
