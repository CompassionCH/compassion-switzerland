##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class TranslationYearlyReport(models.Model):
    _inherit = "translation.daily.report"  # pylint: disable=R7980
    _name = "translation.yearly.report"
    _table = "translation_yearly_report"
    _description = "Yearly translations report"

    def _date_format(self):
        """
         Used to aggregate data in various formats (in subclasses) "
        :return: (date_trunc value, date format)
        """""
        return 'year', 'YYYY'
