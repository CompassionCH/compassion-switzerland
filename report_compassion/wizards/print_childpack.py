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


class PrintChildpack(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """
    _name = 'print.childpack'

    type = fields.Selection([
        ('report_compassion.childpack_full', 'Full Childpack'),
        ('report_compassion.childpack_small', 'Small Childpack'),
    ], default=lambda s: s._default_type())
    lang = fields.Selection(
        '_lang_selection', default=lambda s: s._default_lang())

    @api.model
    def _lang_selection(self):
        languages = self.env['res.lang'].search([])
        return [(language.code, language.name) for language in languages]

    @api.model
    def _default_type(self):
        child = self.env['compassion.child'].browse(self.env.context.get(
            'active_id'))
        if child.sponsor_id:
            return 'report_compassion.childpack_small'
        return 'report_compassion.childpack_full'

    @api.model
    def _default_lang(self):
        child = self.env['compassion.child'].browse(self.env.context.get(
            'active_id'))
        if child.sponsor_id:
            return child.sponsor_id.lang
        return self.env.lang

    @api.multi
    def print_report(self):
        """
        Print selected child dossier
        :return: Generated report
        """
        model = 'compassion.child'
        records = self.env[model].browse(self.env.context.get('active_ids'))
        return self.env['report'].get_action(
            records, self.type, data={
                'lang': self.lang, 'doc_ids': records.ids}
        )
