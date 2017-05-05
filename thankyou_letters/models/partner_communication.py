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

    @api.model
    def create(self, vals):
        """
        Fetch a success story for donation communications
        :param vals: values for record creation
        :return: partner.communication.job record
        """
        job = super(PartnerCommunication, self).create(vals)
        if job.config_id.model == 'account.invoice.line':
            job.set_success_story()
        return job

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

    @api.multi
    def send(self):
        """
        Update donator tag.
        :return: True
        """
        res = super(PartnerCommunication, self).send()
        donator = self.env.ref('partner_compassion.res_partner_category_donor')
        partners = self.filtered(
            lambda j: j.config_id.model == 'account.invoice.line' and
            donator not in j.partner_id.category_id).mapped('partner_id')
        partners.write({'category_id': [(4, donator.id)]})

        return res
