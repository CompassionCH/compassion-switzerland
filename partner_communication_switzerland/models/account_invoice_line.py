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
        override thankyou_letters.get_donations()
        """
        res_name = False
        total = sum(self.mapped("price_subtotal_signed"))
        total_string = f"{total:,.0f}.-" if isinstance(total, int) else f"{total:,.2f}
        total_string.replace(",", "'")

        event_names = self.mapped("event_id.name")
        product_names = self.mapped("product_id.thanks_name")
        gift = "gift" in self.mapped("invoice_id.invoice_category")
        if len(event_names) == 1 and not gift:
            res_name = event_names[0]
        elif not event_names and len(product_names) == 1 and not gift:
            res_name = product_names[0]
        elif len(product_names) > 1:
            res_name = ', '.join([str(elem) for elem in product_names])
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

    @api.multi
    def generate_thank_you(self):
        """
        Do not group communications which have not same event linked.
        Propagate event to the communication and use the creator of the event
        as the default thanker.
        """
        event = self.mapped("event_id")[:1]
        default_communication_config = False
        # Special case for gifts : never put in event donation
        gift = "gift" in self.mapped("invoice_id.invoice_category")
        if event and not gift:
            default_communication_config = self.env.ref(
                "partner_communication_switzerland.config_event_standard"
            )
        res = super(
            AccountInvoiceLine,
            self.with_context(
                same_job_search=[("event_id", "=", event.id)],
                default_event_id=event.id,
                default_user_id=event.mapped("staff_ids.user_ids")[:1].id,
                default_ambassador_id=self.mapped("user_id")[:1].id,
                default_communication_config=default_communication_config
            ),
        ).generate_thank_you()

        return res

    @api.multi
    def send_receipt_to_ambassador(self):
        """
        Generates a receipt for the ambassador informing him or her that he or she
        received a donation.
        :return: True
        """
        ambassador = self.mapped("user_id")
        ambassador.ensure_one()
        ambassador_config = self._get_ambassador_receipt_config()
        if ambassador_config:
            self.env["partner.communication.job"].create(
                {
                    "partner_id": ambassador.id,
                    "object_ids": self.ids,
                    "config_id": ambassador_config.id,
                }
            )
        return True

    @api.multi
    def _get_ambassador_receipt_config(self):
        """
        Returns the correct receipt for ambassador given the donations.
        :return: partner.communication.config record
        """
        return False
