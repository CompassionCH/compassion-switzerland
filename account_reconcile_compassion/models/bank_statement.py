##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class AccountStatement(models.Model):
    """ Adds a relation to a recurring invoicer. """

    _inherit = "account.bank.statement"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(default=lambda b: b._default_name())
    invoice_ids = fields.Many2many(
        "account.invoice",
        string="Invoices",
        compute="_compute_invoices",
        readonly=False,
    )
    generated_invoices_count = fields.Integer("Invoices", compute="_compute_invoices")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _default_name(self):
        """ Find the appropriate sequence """
        journal_id = self.env.context.get("default_journal_id")
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            sequence = self.env["ir.sequence"].search([("name", "=", journal.name)])
            if sequence:
                return sequence.next_by_id()
        return ""

    @api.multi
    def _compute_invoices(self):
        invoice_obj = self.env["account.invoice"]
        for stmt in self:
            invoices = invoice_obj.search([("origin", "=", stmt.name)])
            stmt.invoice_ids = invoices
            stmt.generated_invoices_count = len(invoices)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.multi
    def to_invoices(self):
        self.ensure_one()
        return {
            "name": "Generated Invoices",
            "view_mode": "tree,form",
            "view_type": "form",
            "res_model": "account.invoice",
            "domain": [("origin", "=", self.name)],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "form_view_ref": "account.invoice_form",
                "journal_type": "sale",
            },
        }

    @api.multi
    def unlink(self):
        self.mapped("invoice_ids").filtered(
            lambda i: i.state in ("draft", "open")
        ).action_invoice_cancel()
        return super(AccountStatement, self).unlink()
