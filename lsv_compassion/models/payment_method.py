##############################################################################
#
#    Copyright (C) 2015-2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PaymentMethod(models.Model):
    _inherit = "account.payment.method"

    # General country info field
    lsv_form_pdf = fields.Binary(compute="_compute_lsv_form_pdf")
    lsv_form_filename = fields.Char(compute="_compute_lsv_form_filename")

    # French document
    fr_lsv_form_pdf = fields.Binary(
        string="lsv_form French", attachment=True
    )
    # German document
    de_lsv_form_pdf = fields.Binary(
        string="lsv_form German", attachment=True
    )
    # Italian document
    it_lsv_form_pdf = fields.Binary(
        string="lsv_form Italian", attachment=True
    )
    # English document
    en_lsv_form_pdf = fields.Binary(
        string="lsv_form English", attachment=True
    )

    @api.multi
    def _compute_lsv_form_pdf(self):
        """ Computes the PDF corresponding to the lang, given in the
        environment. English is the default language. """
        lang = self.env.lang[:2]
        field_name = lang + "_lsv_form_pdf"
        for payment_method in self:
            payment_method.lsv_form_pdf = getattr(
                payment_method, field_name, payment_method.en_lsv_form_pdf
            )