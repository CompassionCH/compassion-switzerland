# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields
from odoo.tools import safe_eval
from odoo.addons.queue_job.job import job


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = 'partner.communication.generate.wizard'

    sponsorship_ids = fields.Many2many(
        'recurring.contract', string='Sponsorships',
    )
    res_model = fields.Selection(
        [('res.partner', 'Partners'),
         ('recurring.contract', 'Sponsorships')],
        'Source', default='res.partner', required=True
    )
    partner_source = fields.Selection(
        [('partner_id', 'Payer'),
         ('correspondant_id', 'Correspondent')],
        'Send to', default='correspondant_id', required=True
    )
    # Remove domain filter and handle it in the view
    model_id = fields.Many2one(
        domain=[]
    )

    @api.multi
    def _compute_progress(self):
        s_wizards = self.filtered(
            lambda w: w.res_model == 'recurring.contract')
        for wizard in s_wizards:
            wizard.progress = float(len(wizard.communication_ids) * 100) / (
                len(wizard.sponsorship_ids.mapped(wizard.partner_source)) or 1)
        super(GenerateCommunicationWizard, self-s_wizards)._compute_progress()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('selection_domain', 'force_language')
    def onchange_domain(self):
        if self.res_model == 'recurring.contract':
            if self.force_language and not self.language_added_in_domain:
                domain = self.selection_domain or '[]'
                domain = domain[:-1] + ", ('{}.lang', '=', '{}')]".format(
                    self.partner_source, self.force_language)
                self.selection_domain = domain.replace('[, ', '[')
                self.language_added_in_domain = True
            if self.selection_domain:
                self.sponsorship_ids = self.env['recurring.contract'].search(
                    safe_eval(self.selection_domain))
                self.partner_ids = self.sponsorship_ids.mapped(
                    self.partner_source)
            if not self.force_language:
                self.language_added_in_domain = False
        else:
            super(GenerateCommunicationWizard, self).onchange_domain()

    @api.multi
    def get_preview(self):
        object_ids = self.partner_ids[0].id
        if self.res_model == 'recurring.contract':
            object_ids = self.sponsorship_ids[0].id
        return super(GenerateCommunicationWizard,
                     self.with_context(object_ids=object_ids)).get_preview()

    @job
    def generate_communications(self):
        """ Create the communication records """
        if self.res_model == 'recurring.contract':
            for sponsorship in self.sponsorship_ids:
                self.with_delay().create_communication({
                    'partner_id': getattr(sponsorship, self.partner_source).id,
                    'object_ids': sponsorship.id,
                    'config_id': self.model_id.id,
                    'auto_send': False,
                    'send_mode': self.send_mode,
                    'report_id': self.report_id.id or
                    self.model_id.report_id.id,
                })
            return True
        else:
            return super(GenerateCommunicationWizard,
                         self)._get_communications()
