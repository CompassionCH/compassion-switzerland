##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# pylint: disable=C8101
{
    "name": "Bank Statement Reconcile for Compassion CH",
    "version": "11.0.1.0.0",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "category": "Finance",
    "website": "http://www.compassion.ch",
    "depends": [
        "sponsorship_switzerland",  # compassion-switzerland
        "account_reconcile_create_invoice",  # compassion-accounting
        "account_bank_statement_import_camt_details",  # OCA/bank-statement-import
    ],
    "data": [
        "data/statement_operation.xml",
        "views/account_reconcile_compassion.xml",
        "views/reconcile_fund_wizard_view.xml",
        "views/reconcile_split_payment_wizard_view.xml",
        "views/change_attribution_wizard_view.xml",
        "views/account_invoice_view.xml",
        "views/res_config_view.xml",
        "views/account_journal.xml",
    ],
    "qweb": ["static/src/xml/account_move_reconciliation.xml"],
    "auto_install": False,
    "installable": True,
}
