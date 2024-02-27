##############################################################################
#
#    Copyright (C) 2016-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models

from odoo.addons.sponsorship_compassion.models.product_names import GIFT_CATEGORY


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def get_donations(self):
        """
        Gets a tuple for thank_you communication
        If more than one product, product_name is False
        :return: (total_donation_amount, product_name)
        override thankyou_letters.get_donations()
        """
        res_name = False
        currency = self.mapped("currency_id")[:1].name
        total = sum(self.mapped("price_subtotal"))
        total_string = f"{total:,.0f}.-" if total.is_integer() else f"{total:,.2f}"
        total_string = currency + " " + total_string.replace(",", "'")

        event_names = self.mapped("event_id.name")
        product_names = self.mapped("product_id.thanks_name")
        gift = "gift" in self.mapped("move_id.invoice_category")
        if len(event_names) == 1 and not gift:
            res_name = event_names[0]
        elif not event_names and len(product_names) == 1 and not gift:
            res_name = product_names[0]
        elif len(product_names) > 1:
            res_name = ", ".join([str(elem) for elem in product_names])
        # Special case for gifts : mention it's a gift even if several
        # different gifts are made.
        else:
            categories = list(
                set(self.with_context(lang="en_US").mapped("product_id.categ_name"))
            )
            if len(categories) == 1 and categories[0] == GIFT_CATEGORY:
                gift_template = self.env.ref(
                    "sponsorship_switzerland.product_template_fund_kdo"
                )
                gift = self.env["product.product"].search(
                    [("product_tmpl_id", "=", gift_template.id)], limit=1
                )
                res_name = gift.thanks_name

        return total_string, res_name
