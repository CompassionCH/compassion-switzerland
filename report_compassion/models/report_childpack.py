##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields

logger = logging.getLogger(__name__)


class ReportChildpackFull(models.AbstractModel):
    """
    Model used to generate childpack in selected language
    """
    _name = 'report.report_compassion.childpack_full'
    _description = "Used to generate childpack in selected language"

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.childpack_full')

    @api.model
    def get_report_values(self, docids, data=None):
        if not data:
            data = {}
        if not docids and data['doc_ids']:
            docids = data['doc_ids']
        lang = data.get('lang', self.env.lang)
        report = self._get_report()
        docs = self.env[report.model].with_context(lang=lang).browse(docids)

        data.update({
            'doc_model': report.model,
            'docs': docs.with_context(lang=lang)
        })
        # Update project information if data is old
        date_limit = date.today() - relativedelta(days=30)
        for project in docs.mapped('project_id').filtered(
                lambda p: not p.last_update_date or p.last_update_date <
                          fields.Date.to_string(date_limit) or not p.country_id
        ):
            project.with_context(async_mode=False).update_informations()

        return data


# pylint: disable=R7980
class ReportChildpackSmall(models.AbstractModel):
    _inherit = 'report.report_compassion.childpack_full'
    _name = 'report.report_compassion.childpack_small'

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.childpack_small')


class ReportChildpackMini(models.AbstractModel):
    _inherit = 'report.report_compassion.childpack_full'
    _name = 'report.report_compassion.childpack_mini'

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.childpack_mini')
