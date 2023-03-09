#    Copyright (C) 2022 Compassion CH
#    @author: Emanuel Cino

from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def generate_crowdfunding_receipt(self):
        """ Generates the receipt communication for a TOGETHER donation,
        only if the donation receipt is not already sent.
        :return: partner.communication.job record
        """
        self.ensure_one()
        if self.communication_id.state == "done":
            return self.communication_id

        comm_obj = self.env["partner.communication.job"]
        config = self.env.ref(
            "crowdfunding_compassion.config_donation_successful_email_template"
        )
        # update the all time impact
        for product_tmpl in self.mapped("invoice_line_ids.product_id.product_tmpl_id"):
            product_tmpl.recompute_amount()

        return comm_obj.create({
            "config_id": config.id,
            "partner_id": self.partner_id.id,
            "object_ids": self.ids
        })
