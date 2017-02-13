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
    success_story_id = fields.Many2one('success.story', 'Success Story')

    @api.model
    def create(self, vals):
        """
        Fetch a success story for donation communications
        :param vals: values for record creation
        :return: partner.communication.job record
        """
        job = super(PartnerCommunication, self).create(vals)
        job._set_success_story()
        return job

    @api.multi
    def refresh_text(self, refresh_uid=False):
        """
        Refresh the success story as well
        :param refresh_uid: User that refresh
        :return: True
        """
        super(PartnerCommunication, self).refresh_text(refresh_uid)
        self._set_success_story()
        return True

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
        Update the count of succes story prints when sending a receipt.
        Update donator tag.
        :return: True
        """
        res = super(PartnerCommunication, self).send()
        for job in self.filtered('success_story_id').filtered('sent_date'):
            job.success_story_id.print_count += 1

        donator = self.env.ref('partner_compassion.res_partner_category_donor')
        for job in self.filtered(lambda j: j.config_id.model ==
                                 'account.invoice.line'):
            job.partner_id.category_id += donator

        return res

    @api.multi
    def _set_success_story(self):
        for job in self:
            if job.config_id.model == 'account.invoice.line':
                story = self.env['success.story'].search([
                    ('is_active', '=', True)]).sorted(
                    lambda s: s.current_usage_count)
                if story:
                    job.success_story_id = story[0]
