##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta
from enum import Enum
from postfinancecheckout import Configuration
from postfinancecheckout.api.transaction_service_api import TransactionServiceApi

from odoo import api, models, fields, _
from odoo.tools import ormcache


class Provider(Enum):
    WORLDLINE = "WORLDLINE SCHWEIZ AG"
    PF_CARD = "POSTFINANCE CARD"
    TWINT = "TWINT"
    E_FINANCE = "POSTFINANCE E-FINANCE"


PF_MAPPING = {
    Provider.WORLDLINE: "SIX Acquiring",
    Provider.PF_CARD: "PostFinance Acquiring - PostFinance Card",
    Provider.E_FINANCE: "PostFinance Acquiring - PostFinance E-Finance",
    Provider.TWINT: "TWINT - TWINT Connector"
}


class ReconcileFundWizard(models.TransientModel):

    _name = "reconcile.1015.wizard"
    _description = "Wizard reconcile 1015 account"

    account_id = fields.Many2one(
        "account.account", "Reconcile account",
        default=lambda s: s.env["account.account"].search([
            ("code", "=", "1015")], limit=1)
    )
    full_reconcile_line_ids = fields.Many2many(
        "account.move.line", "reconcile_1015_reconciled", string="Reconciled lines",
        readonly=True
    )
    partial_reconcile_line_ids = fields.Many2many(
        "account.move.line", "reconcile_1015_partial_reconciled",
        string="Partial reconciled lines", readonly=True
    )
    missing_donation_line_ids = fields.Many2many(
        "account.move.line", "reconcile_1015_missing_invoice",
        string="Leftover donations",
        readonly=True
    )

    def reconcile_1015(self):
        mvl_obj = self.env["account.move.line"]
        credit_lines = mvl_obj.search([
            ("account_id", "=", self.account_id.id),
            ("full_reconcile_id", "=", False),
            ("credit", ">", 0),
            ("date", ">=", "2022-02-09")  # Date of activation of pf_checkout
        ])
        for cl in credit_lines:
            self.reconcile_using_pf_checkout(cl)

        # Compute results
        if self.partial_reconcile_line_ids:
            oldest_credit = min(self.partial_reconcile_line_ids.mapped("date"))
            self.missing_donation_line_ids = mvl_obj.search([
                ("account_id", "=", self.account_id.id),
                ("full_reconcile_id", "=", False),
                ("debit", ">", 0),
                ("date", "<=", fields.Date.to_string(oldest_credit)),
                ("date", ">=", "2022-02-09")  # Date of activation of pf_checkout
            ]).filtered(lambda m: not m.matched_credit_ids)
        if self.full_reconcile_line_ids:
            self.env.user.notify_success(
                message=_("Successfully reconciled %s entries")
                % len(self.full_reconcile_line_ids),
                sticky=True
            )
        else:
            if not credit_lines:
                self.env.user.notify_success(
                    message=_("Every credit entry is reconciled"))
            else:
                self.env.user.notify_warning(
                    message=_("0 credit entry could be fully reconciled"))
        return {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "view_type": "form",
            "res_model": "account.move.line",
            "target": "current",
            "context": self.env.context,
            "domain": [("id", "in", (self.partial_reconcile_line_ids +
                                     self.missing_donation_line_ids).ids)]
        }

    @api.multi
    def reconcile_using_pf_checkout(self, move_line):
        # Transactions are grouped by dates
        date_position = -1
        date_length = 8
        search_days_delta = 0
        if Provider.WORLDLINE.value in move_line.name:
            date_position = self._search_in_credit_string(move_line, "REFERENCES: ")
            search_days_delta = -9
            provider = Provider.WORLDLINE
        elif Provider.TWINT.value in move_line.name:
            date_position = self._search_in_credit_string(move_line, "Payout ")
            search_days_delta = -1
            provider = Provider.TWINT
        elif Provider.PF_CARD.value in move_line.name:
            date_position = self._search_in_credit_string(move_line, " TRAITEMENT DU ")
            date_length = 10
            provider = Provider.PF_CARD
        elif Provider.E_FINANCE.value in move_line.name:
            date_position = self._search_in_credit_string(move_line, " TRAITEMENT DU ")
            date_length = 10
            provider = Provider.E_FINANCE
        if date_position == -1:
            self.missing_donation_line_ids += move_line
            return False
        date_transactions = datetime.strptime(
            move_line.name[date_position:date_position + date_length],
            "%Y%m%d" if date_length == 8 else "%d.%m.%Y"
        ) + timedelta(days=search_days_delta)
        pf_service, space_id = self.get_pf_service()
        debit_match = self.env["account.move.line"]
        pf_filter = self.get_pf_filter(date_transactions, provider)
        for transaction in pf_service.search(space_id, pf_filter):
            # Some references have this TEMPTR- prefix that should be ignored
            ref = transaction.merchant_reference.replace("TEMPTR-", "").split("-")[0]
            debit_match += self.env["account.move.line"].search([
                ("ref", "like", ref),
                ("debit", ">", 0),
                ("full_reconcile_id", "=", False),
                ("account_id", "=", self.account_id.id)
            ]).filtered(lambda m: not m.matched_credit_ids)
        # Perform a partial or full reconcile
        (move_line + debit_match).reconcile()
        if sum(debit_match.mapped("debit")) == move_line.credit:
            self.full_reconcile_line_ids += move_line
        else:
            self.partial_reconcile_line_ids += move_line
        return True

    @api.model
    def _search_in_credit_string(self, move_line, search_string):
        string_position = move_line.name.find(search_string)
        if string_position > -1:
            string_position += len(search_string)
        return string_position

    @ormcache()
    def get_pf_service(self):
        pf_acquirer = self.env.ref(
            "payment_postfinance_flex.payment_acquirer_postfinance")
        config = Configuration(
            user_id=pf_acquirer.postfinance_api_userid,
            api_secret=pf_acquirer.postfinance_api_application_key)
        return TransactionServiceApi(configuration=config),\
            pf_acquirer.postfinance_api_spaceid

    @api.model
    def get_pf_filter(self, date_search=None, provider=None, state="FULFILL"):
        if date_search is None:
            date_search = datetime.today()
        stop = date_search.replace(hour=23, minute=0, second=0, microsecond=0)
        start = stop + timedelta(days=-1)
        domain = {
            "filter": {
                "children": [
                    {
                        "fieldName": "createdOn",
                        "operator": "GREATER_THAN",
                        "type": "LEAF",
                        "value": start.isoformat(),
                    },
                    {
                        "fieldName": "createdOn",
                        "operator": "LESS_THAN_OR_EQUAL",
                        "type": "LEAF",
                        "value": stop.isoformat(),
                    },
                    {
                        "fieldName": "state",
                        "operator": "EQUALS",
                        "type": "LEAF",
                        "value": state,
                    }
                ],
                "type": "AND",
            }
        }
        if provider is not None:
            domain["filter"]["children"].append({
                "fieldName": "paymentConnectorConfiguration.name",
                "operator": "CONTAINS",
                "type": "LEAF",
                "value": PF_MAPPING.get(provider),
            })
        return domain
