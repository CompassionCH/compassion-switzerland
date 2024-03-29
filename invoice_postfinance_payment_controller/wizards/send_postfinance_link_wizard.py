##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import api, models, fields


class SendPostfinanceLinkWizard(models.TransientModel):
    _name = "account.invoice.send.postfinance.link.wizard"
    _description = "Wizard send invoice postfinance"

    invoice_ids = fields.Many2many(
        "account.invoice",
        "account_invoice_send_postfinance_link_wizard_rel",
        string="Related invoices",
        default=lambda self: self._default_invoices(),
        readonly=False,
    )
    state = fields.Selection(
        [
            ("single", "Single invoice"),
            ("multi", "Multiple invoices"),
            ("invalid_partner", "Too much partners"),
            ("invalid_invoice", "Invalid invoice selection"),
        ],
        compute="_compute_state",
    )
    origin = fields.Char(compute="_compute_origin", inverse="_inverse_origin")

    def _default_invoices(self):
        return (
            self.env["account.invoice"]
            .browse(self.env.context.get("active_ids"))
            .filtered(lambda i: i.state == "open")
        )

    @api.depends("invoice_ids")
    def _compute_state(self):
        for wizard in self:
            if len(wizard.invoice_ids) > 1:
                if len(wizard.invoice_ids.mapped("partner_id")) > 1:
                    wizard.state = "invalid_partner"
                else:
                    wizard.state = "multi"
            elif wizard.invoice_ids:
                wizard.state = "single"
            else:
                wizard.state = "invalid_invoice"

    def _compute_origin(self):
        for wizard in self:
            wizard.origin = " ".join(
                wizard.invoice_ids.filtered("origin").mapped("origin")
            )

    def _inverse_origin(self):
        for wizard in self:
            wizard.invoice_ids[:1].origin = wizard.origin
            wizard.invoice_ids[1:].write({"origin": False})

    @api.multi
    def generate_communication(self):
        self.ensure_one()
        partner = self.invoice_ids.mapped("partner_id")
        partner.ensure_one()
        if self.state == "multi":
            self._merge_invoices()
        self.invoice_ids.ensure_one()
        config_id = self.env.ref(
            "invoice_postfinance_payment_controller.invoice_online_payment_config"
        ).id
        communication = self.env["partner.communication.job"].create(
            {
                "config_id": config_id,
                "partner_id": partner.id,
                "object_ids": self.invoice_ids.id,
            }
        )
        # Inject success_url and error_url inside the communication
        new_link = self.invoice_ids.sudo().get_portal_url()
        link_pattern = re.compile(r"/compassion/payment/invoice/\d+")
        communication.body_html = link_pattern.sub(new_link, communication.body_html)
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "partner.communication.job",
            "context": self.env.context,
            "res_id": communication.id,
        }

    def _merge_invoices(self):
        result_invoice = self.invoice_ids[:1]
        other_invoices = self.invoice_ids[1:]
        self.invoice_ids.action_invoice_cancel()
        other_invoices.mapped("invoice_line_ids").write(
            {"invoice_id": result_invoice.id}
        )
        result_invoice.action_invoice_draft()
        result_invoice.action_invoice_open()
        self.invoice_ids = result_invoice
