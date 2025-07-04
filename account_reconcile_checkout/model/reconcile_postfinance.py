from odoo import models, api
import logging
from datetime import datetime, timedelta
from enum import Enum
import re

from postfinancecheckout import Configuration
from postfinancecheckout.api import TransactionServiceApi, ChargeBankTransactionServiceApi

_logger = logging.getLogger(__name__)

class Provider(Enum):
    WORLDLINE = "WORLDLINE SCHWEIZ AG"
    PF_CARD = "POSTFINANCE CARD"
    TWINT = "TWINT"
    E_FINANCE = "POSTFINANCE E-FINANCE"
    PF_PAY = "POSTFINANCE PAY"

PF_MAPPING = {
    Provider.WORLDLINE: "SIX Acquiring",
    Provider.PF_CARD: "PostFinance Acquiring - PostFinance Card",
    Provider.E_FINANCE: "PostFinance Acquiring - PostFinance E-Finance",
    Provider.PF_PAY: "PostFinance Acquiring - PostFinance Pay",
    Provider.TWINT: "TWINT - TWINT Connector",
}

class PostfinanceReconcileWizard(models.TransientModel):
    _name = 'postfinance.reconcile.wizard'
    _description = 'PostFinance Reconcile Wizard'

    def get_pf_filter(self, date_search=None, provider=None, state="SETTLED", transaction=""):
        if date_search is None:
            date_search = datetime.today()
        if provider and provider.name == "TWINT":
            stop = date_search.replace(hour=23, minute=0, second=0, microsecond=0)
            start = stop + timedelta(days=-1)
        else:
            stop = date_search.replace(hour=23, minute=59, second=59, microsecond=999999)
            start = date_search.replace(hour=0, minute=0, second=0, microsecond=0)
        domain = {
            "filter": {
                "children": [
                    {
                        "fieldName": f"{transaction}completedOn",
                        "operator": "GREATER_THAN",
                        "type": "LEAF",
                        "value": start.isoformat(),
                    },
                    {
                        "fieldName": f"{transaction}completedOn",
                        "operator": "LESS_THAN_OR_EQUAL",
                        "type": "LEAF",
                        "value": stop.isoformat(),
                    },
                ],
                "type": "AND",
            }
        }
        if provider is not None:
            domain["filter"]["children"].append(
                {
                    "fieldName": f"{transaction}paymentConnectorConfiguration.name",
                    "operator": "CONTAINS",
                    "type": "LEAF",
                    "value": PF_MAPPING.get(provider),
                }
            )
        return domain

    def search_and_rec_with_pf_service(self, config, space_id, payout_date, provider, credit_ml, ml_obj, pf_api_service, filter_option):
        try:
            trans = pf_api_service.search(space_id, self.get_pf_filter(payout_date, provider, transaction=filter_option))
            debit_ml_ids = ml_obj.browse()  # empty recordset
            for tr in trans:
                if filter_option != "":
                    merchant_reference = tr.transaction.merchant_reference
                    amount = tr.transaction_currency_amount
                else:
                    merchant_reference = tr.merchant_reference
                    amount = tr.authorization_amount
                aml = ml_obj.search([
                    ("account_id.code", "=", "44"),
                    "|",
                    ("name", "ilike", merchant_reference),
                    ("ref", "ilike", merchant_reference)
                ])
                if aml:
                    _logger.info(f"Found: {merchant_reference} with debit of: {aml.debit} for transaction amount of {amount}")
                    self.env['postfinance.reconcile.log'].create({
                        'message': f"Found: {merchant_reference} with debit of: {aml.debit} for transaction amount of {amount}",
                        'log_type': 'info',
                    })
                    debit_ml_ids += aml
                else:
                    warning_msg = f"Not found: {merchant_reference}"
                    _logger.warning(warning_msg)
                    self.env['postfinance.reconcile.log'].create({
                        'message': warning_msg,
                        'log_type': 'warning',
                    })
            if round(sum(debit_ml_ids.mapped("debit")), 2) == credit_ml.credit:
                (credit_ml + debit_ml_ids).remove_move_reconcile()
                (credit_ml + debit_ml_ids).reconcile()
                success_msg = f"{len(credit_ml + debit_ml_ids)} move lines reconciled"
                _logger.info(success_msg)
                self.env['postfinance.reconcile.log'].create({
                    'message': success_msg,
                    'log_type': 'info',
                })
            else:
                warning_msg = f"Not matching credit: {credit_ml.credit} on {credit_ml.date} with label: {credit_ml.name}"
                _logger.warning(warning_msg)
                self.env['postfinance.reconcile.log'].create({
                    'message': warning_msg,
                    'log_type': 'warning',
                })
                if debit_ml_ids:
                    sum_msg = f"Sum of invoices: {sum(debit_ml_ids.mapped('debit'))}"
                    _logger.warning(sum_msg)
                    self.env['postfinance.reconcile.log'].create({
                        'message': sum_msg,
                        'log_type': 'warning',
                    })
                    for d in debit_ml_ids:
                        candidate_msg = f"Candidate matching: {d.debit} on {d.date} with label: {d.name}"
                        _logger.warning(candidate_msg)
                        self.env['postfinance.reconcile.log'].create({
                            'message': candidate_msg,
                            'log_type': 'warning',
                        })
        except Exception as e:
            error_msg = f"Error during reconciliation for {credit_ml.name}: {str(e)}"
            _logger.error(error_msg)
            self.env['postfinance.reconcile.log'].create({
                'message': error_msg,
                'log_type': 'error',
            })

    @api.model
    def action_reconcile(self):
        try:
            pf_acquirer = self.env.ref(
                "payment_postfinance_flex.payment_acquirer_postfinance"
            )
            config = Configuration(
                user_id=pf_acquirer.postfinance_api_userid,
                api_secret=pf_acquirer.postfinance_api_application_key,
                default_headers={'x-meta-custom-header': 'value-1', 'x-meta-custom-header-2': 'value-2'},
                request_timeout=30
            )
            space_id = pf_acquirer.postfinance_api_spaceid

            ml_obj = self.env["account.move.line"]
            credit_ml_ids = ml_obj.search([
                ("account_id.code", "=", "44"),
                ("full_reconcile_id", "=", False),
                ("debit", "=", 0),
                ("parent_state", "=", "posted")
            ])

            ts = TransactionServiceApi(configuration=config)
            cbts = ChargeBankTransactionServiceApi(configuration=config)

            for credit_ml in credit_ml_ids:
                if re.match(".*Payout ([0-9]*) *Gross", credit_ml.name):
                    provider = Provider.TWINT
                    payout_re = re.match(".*Payout ([0-9]*) *Gross", credit_ml.name)
                    if payout_re:
                        payout_date = datetime.strptime(payout_re[1], '%Y%m%d') - timedelta(days=1)
                        self.search_and_rec_with_pf_service(config, space_id, payout_date, provider, credit_ml, ml_obj, cbts, "transaction.")
                elif re.match(r".*POSTFINANCE CARD TRAITEMENT DU ([0-9]+(\.[0-9]+)+) COMPASSION.*", credit_ml.name):
                    provider = Provider.PF_CARD
                    payout_re = re.match(r".*TRAITEMENT DU ([0-9]+(\.[0-9]+)+) COMPASSION.*", credit_ml.name)
                    payout_date = datetime.strptime(payout_re[1], '%d.%m.%Y')
                    self.search_and_rec_with_pf_service(config, space_id, payout_date, provider, credit_ml, ml_obj, cbts, "transaction.")
                elif re.match(r".*POSTFINANCE PAY TRAITEMENT DU ([0-9]+(\.[0-9]+)+) COMPASSION.*", credit_ml.name):
                    provider = Provider.PF_PAY
                    payout_re = re.match(r".*TRAITEMENT DU ([0-9]+(\.[0-9]+)+) COMPASSION.*", credit_ml.name)
                    payout_date = datetime.strptime(payout_re[1], '%d.%m.%Y')
                    self.search_and_rec_with_pf_service(config, space_id, payout_date, provider, credit_ml, ml_obj, cbts, "transaction.")
                elif re.match(r'.*DAT\.([0-9]+(\.[0-9]+)+)/Compassion Suisse.*', credit_ml.name):
                    provider = Provider.WORLDLINE
                    payout_re = re.match(r'.*DAT\.([0-9]+(\.[0-9]+)+)/Compassion Suisse.*', credit_ml.name)
                    payout_date = datetime.strptime(payout_re[1], '%d.%m.%Y') - timedelta(days=9)
                    self.search_and_rec_with_pf_service(config, space_id, payout_date, provider, credit_ml, ml_obj, ts, "")
                else:
                    warning_msg = f"No case for: {credit_ml.name}"
                    _logger.warning(warning_msg)
                    self.env['postfinance.reconcile.log'].create({
                        'message': warning_msg,
                        'log_type': 'warning',
                    })
        except Exception as e:
            error_msg = f"Error in action_reconcile: {str(e)}"
            _logger.error(error_msg)
            self.env['postfinance.reconcile.log'].create({
                'message': error_msg,
                'log_type': 'error',
            })