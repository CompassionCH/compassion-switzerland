##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import date


from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PrintTaxReceipt(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """
    _name = 'print.tax_receipt'
    _description = "Select a tax receipt"

    state = fields.Selection([('new', 'new'), ('pdf', 'pdf')], default='new')
    year = fields.Integer(default=date.today().year - 1)
    pdf = fields.Boolean()
    pdf_name = fields.Char(default='tax_receipt.pdf')
    pdf_download = fields.Binary(readonly=True)

    @api.onchange
    def onchange_year(self):
        this_year = date.today().year
        if self.year >= this_year:
            return {
                'warning': {
                    'title': _("Year is incomplete"),
                    'message': _("Payments for the selected year are not yet "
                                 "registered completely. The tax receipt may "
                                 "be incomplete.")
                }
            }

    @api.multi
    def get_report(self):
        """
        Call when button 'Get Report' clicked.
        Print tax receipt
        :return: Generated report
        """
        model = 'res.partner'
        records = self.env[model].browse(self.env.context.get('active_ids'))
        data = {
            'doc_ids': records.ids,
            'year': self.year,
        }
        lang = records.mapped('lang')
        if len(lang) == 1:
            data['lang'] = lang[0]
        else:
            raise UserError(_(
                "You can only generate tax certificate for one language at "
                "a time."))
        report_ref = self.env.ref('report_compassion.tax_receipt_report')
        if self.pdf:
            pdf_data = report_ref.report_action(self, data=data)
            self.pdf_download = base64.encodebytes(
                report_ref.render_qweb_pdf(
                    pdf_data['data']['doc_ids'], pdf_data['data'])[0])

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

        return report_ref.report_action(self, data=data)
