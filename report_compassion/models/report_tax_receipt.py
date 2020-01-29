##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date

from odoo import api, models


class ReportTaxReceipt(models.AbstractModel):
    """
    Model used to generate tax receipt
    """
    _name = 'report.report_compassion.tax_receipt'
    _description = "Used to generate tax receipt"

    @api.multi
    def render_html(self, docids, data=None):
        """
        :param data: data collected from the print wizard.
        :return: html rendered report
        """
        if not data:
            data = {
                'year': date.today().year,
                'lang': self.env.context.get('lang', 'en_US')
            }
        # We must retrieve the text of the receipt from the mail_template
        template = self.env.ref(
            'report_compassion.tax_receipt_template'
        ).with_context(year=data['year'], lang=data['lang'])
        texts = template.render_template(
            template.body_html, 'res.partner', docids)
        lang = data.get('lang', self.env.lang)
        report = self.env['report']._get_report_from_name(
            'report_compassion.tax_receipt')
        data.update({
            'doc_model': report.model,
            'docs': self.env[report.model].with_context(lang=lang).browse(
                docids),
            'texts': texts,
            'subject': template.subject,
        })

        return self.env['report'].with_context(lang=lang).render(
            report.report_name, data)
