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
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
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
    "name": "Tailor Sponsorships to Compassion CH needs",
    "version": "14.0.2.0.0",
    "category": "Other",
    "author": "Compassion CH",
    "maintainers": ["ecino"],
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "depends": [
        "l10n_ch_isrb",  # OCA/l10n-switzerland
        "crm_compassion",  # compassion-modules
        "partner_auto_match",  # compassion-modules
        "sponsorship_sub_management",  # compassion-modules
        "account_banking_mandate",  # oca_addons/bank-payment
        "partner_compassion",  # compassion-switzerland
        "account_statement_completion",  # compassion-accounting
        "gift_compassion",  # compassion-modules
        "web_notify",  # oca_addons/web
        "sbc_compassion",  # compassion-modules
    ],
    "demo": ["data/demo_journal.xml", "data/demo_account.xml"],
    "data": [
        "data/product.xml",
        "data/pricelists.xml",
        "data/completion_rules.xml",
        "data/sequence.xml",
        "data/partner_category_data.xml",
        "data/payment_modes.xml",
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/contract_view.xml",
        "views/postpone_waiting_reminder_wizard_view.xml",
        "views/correspondence_view.xml",
        "views/gift_compassion_view.xml",
        "views/product_template_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
