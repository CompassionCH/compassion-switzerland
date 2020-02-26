##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api
from odoo.addons.sponsorship_compassion.models.product_names import GIFT_CATEGORY


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def get_donations(self):
        """
        Gets a tuple for thank_you communication
        If more than one product, product_name is False
        :return: (total_donation_amount, product_name)
        """
        res_name = False
        total = sum(self.mapped('price_subtotal'))
        total_string = f"{int(total):,}".replace(',', "'")

        event_names = self.mapped('event_id.name')
        product_names = self.mapped('product_id.thanks_name')
        gift = 'gift' in self.mapped('invoice_id.invoice_type')
        if len(event_names) == 1 and not gift:
            res_name = event_names[0]
        elif not event_names and len(product_names) == 1 and not gift:
            res_name = product_names[0]
        # Special case for gifts : mention it's a gift even if several
        # different gifts are made.
        else:
            categories = list(set(self.with_context(lang='en_US').mapped(
                'product_id.categ_name')))
            if len(categories) == 1 and categories[0] == GIFT_CATEGORY:
                gift_template = self.env.ref(
                    'sponsorship_switzerland.product_template_fund_kdo')
                gift = self.env['product.product'].search([
                    ('product_tmpl_id', '=', gift_template.id)
                ], limit=1)
                res_name = gift.thanks_name

        return total_string, res_name

    @api.multi
    def generate_thank_you(self):
        """
        Do not group communications which have not same event linked.
        Propagate event to the communication and use the creator of the event
        as the default thanker.
        """
        event = self.mapped('event_id')[:1]
        user = event.mapped('staff_ids.user_ids')[:1] or event.create_uid
        return super(AccountInvoiceLine, self.with_context(
            same_job_search=[('event_id', '=', event.id)],
            default_event_id=event.id,
            default_user_id=user.id
        )).generate_thank_you()

    @api.multi
    def get_default_thankyou_config(self):
        """
        Returns the default communication configuration.
        Choose event communication if the donations are linked to an event
        :return: partner.communication.config record
        """
        # Special case for gifts : never put in event donation
        gift = 'gift' in self.mapped('invoice_id.invoice_type')
        if self.mapped('event_id') and not gift:
            return self.env.ref('partner_communication_switzerland.'
                                'config_event_standard')
        return super().get_default_thankyou_config()
