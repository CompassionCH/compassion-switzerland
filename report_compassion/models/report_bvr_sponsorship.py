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

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import Warning as odooWarning

logger = logging.getLogger(__name__)


class BvrSponsorship(models.AbstractModel):
    """
    Model used for preparing data for the bvr report. It can either
    generate 3bvr report, 2bvr report or single bvr report.
    """
    _name = 'report.report_compassion.bvr_sponsorship'
    _description = "Used for preparing data for a 3BVR " \
                   "or single BVR report (sponsorship)"

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.bvr_sponsorship')

    def _get_default_data(self):
        """
        If no data is given for the report, use default values.
        :return: default mandatory data for the bvr report.
        """
        print_bvr_obj = self.env['print.sponsorship.bvr']
        return {
            'date_start': print_bvr_obj.default_start(),
            'date_stop': print_bvr_obj.default_stop(),
            'preprinted': False,
        }

    @api.model
    def get_report_values(self, docids, data=None):
        report = self._get_report()
        final_data = self._get_default_data()
        if data:
            final_data.update(data)
            if not docids and data['doc_ids']:
                docids = data['doc_ids']

        start = fields.Datetime.from_string(final_data['date_start'])
        stop = fields.Datetime.from_string(final_data['date_stop'])

        # Months will contain all months we want to include for payment.
        months = list()
        while start <= stop:
            months.append(fields.Datetime.to_string(start))
            start = start + relativedelta(months=1)

        sponsorships = self.env['recurring.contract'].browse(docids)
        sponsorships = sponsorships.filtered(
            lambda s: s.state not in ('terminated', 'cancelled'))
        groups = sponsorships.mapped('group_id')
        if not groups or not months:
            raise odooWarning(
                _("Selection not valid. No active sponsorship found."))

        # Docs will contain the groups for which we have to print the payment
        # slip : {'recurring.contract.group': 'recurring.contract' recordset}
        docs = dict()
        for group in groups:
            docs[group] = sponsorships.filtered(lambda s: s.group_id == group)
        final_data.update({
            'doc_model': report.model,  # recurring.contract.group
            'doc_ids': groups.ids,
            'docs': docs,
            'months': months
        })
        return final_data


# pylint: disable=consider-merging-classes-inherited
class TwoBvrSponsorship(models.AbstractModel):
    _inherit = 'report.report_compassion.bvr_sponsorship'
    _name = 'report.report_compassion.2bvr_sponsorship'

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.2bvr_sponsorship')


# pylint: disable=consider-merging-classes-inherited
class ThreeBvrSponsorship(models.AbstractModel):
    _inherit = 'report.report_compassion.bvr_sponsorship'
    _name = 'report.report_compassion.3bvr_sponsorship'

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.3bvr_sponsorship')

    @api.model
    def get_report_values(self, docids, data=None):
        """ Include setting for telling 3bvr paper has offset between
                payment slips.
                """
        if data is None:
            data = dict()
        data['offset'] = 1
        return super().get_report_values(docids, data)


class BvrSponsorshipDue(models.AbstractModel):
    """
    Allows to send custom data to report.
    """
    _name = 'report.report_compassion.bvr_due'

    @api.model
    def get_report_values(self, docids, data=None):
        """
        :param data: data collected from the print wizard.
        :return: html rendered report
        """
        if not data:
            data = {'doc_ids': docids}
        lang = data.get('lang', self.env.lang)
        data.update({
            'doc_model': 'recurring.contract',
            'docs': self.env['recurring.contract'].with_context(
                lang=lang).browse(docids),
        })
        return data
