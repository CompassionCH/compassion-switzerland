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
    _inherit = 'mail.template'

    report_product_id = fields.Many2one(
        'product.product', 'Product for report')

    @api.multi
    def generate_email(self, res_ids, fields=None):
        """
        Pass the product in the context for generating donation payment
        slips.
        """
        self.ensure_one()
        return super(MailTemplate, self.with_context(
            report_product_id=self.report_product_id.id)
        ).generate_email(res_ids, fields)

    @api.model
    def refresh_sendgrid_tracking(self):
        """
        Method that refreshes the sendgrid templates and update
        tracked url in the corresponding mail.templates
        :return: True
        """
        self.env['sendgrid.template'].update_templates()
        templates = self.search([
            ('sendgrid_template_ids', '!=', False)
        ])
        templates.update_substitutions()
        communication_campaign_id = self.env.ref(
            'partner_communication_switzerland.utm_campaign_communication').id
        medium_id = self.env.ref('utm.utm_medium_email').id
        for template in templates:
            # Find wp substitutions without value
            to_track = template.substitution_ids.filtered(
                lambda s: '{wp' in s.key and not s.value)
            source = self.env['partner.communication.config'].search([
                ('email_template_id', '=', template.id),
                ('send_mode', 'not in', ['physical', 'auto_physical', 'none'])
            ], limit=1)
            to_track.replace_tracking_link(
                campaign_id=communication_campaign_id,
                medium_id=medium_id,
                source_id=source.source_id.id
            )
        return True
