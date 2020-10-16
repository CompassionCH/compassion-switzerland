##############################################################################
#
#    Copyright (C) 2017-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class MailTemplate(models.Model):
    _inherit = "mail.template"

    report_product_id = fields.Many2one(
        "product.product", "Product for report", readonly=False
    )
    mailchimp_template_ids = fields.One2many(
        "mailchimp.email.lang.template", "email_template_id", "Mailchimp templates"
    )

    @api.multi
    def generate_email(self, res_ids, fields=None):
        """
        Pass the product in the context for generating donation payment
        slips.
        """
        self.ensure_one()
        return super(
            MailTemplate, self.with_context(report_product_id=self.report_product_id.id)
        ).generate_email(res_ids, fields)
