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
import base64
from datetime import datetime

from openerp.tools import relativedelta

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
    state = fields.Selection([('new', 'new'), ('pdf', 'pdf')], default='new')
    pdf = fields.Boolean()
    pdf_name = fields.Char(default='fund.pdf')
    pdf_download = fields.Binary(readonly=True)

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
        # Prevent printing dossier if completion date is in less than 2 years
        in_two_years = datetime.today() + relativedelta(years=2)
        records = self.env[model].browse(self.env.context.get(
            'active_ids')).filtered(
            lambda c: c.state in ('N', 'I', 'P') and c.desc_en and
            (not c.completion_date or fields.Datetime.from_string(
                c.completion_date) > in_two_years)
        )
        data = {
            'lang': self.lang,
            'doc_ids': records.ids
        }
        if self.pdf:
            name = records.local_id if len(records) == 1 else 'dossiers'
            self.pdf_name = name + '.pdf'
            self.pdf_download = base64.b64encode(
                self.env['report'].with_context(
                    must_skip_send_to_printer=True).get_pdf(
                        records.ids, self.type, data=data))
            self.state = 'pdf'
            return {
                'name': 'Download report',
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }
        return self.env['report'].get_action(records, self.type, data=data)
