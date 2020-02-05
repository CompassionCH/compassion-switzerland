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
    'name': 'Tailor Sponsorships to Compassion CH needs',
    'version': '11.0.0.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'crm_compassion',                   # compassion-modules
        'sponsorship_tracking',             # compassion-modules
        'account_payment_line_cancel',      # oca_addons/bank-payment
        'partner_compassion',               # compassion-switzerland
        'account_statement_completion',     # compassion-accounting
        'l10n_ch_pain_direct_debit',        # l10n-switzerland
        'l10n_ch_payment_slip',             # l10n-switzerland
        'gift_compassion',                  # compassion-modules
        'donation_report_compassion',       # compassion-accounting
        'web_notify',                       # oca_addons/web
        'sbc_compassion'                    # compassion-modules
    ],
    'demo': [
        'data/demo_journal.xml',
        'data/demo_account.xml'
    ],
    'data': [
        'data/product.xml',
        'data/completion_rules.xml',
        'data/payment_methods.xml',
        'data/payment_modes.xml',
        'data/sequence.xml',
        'data/partner_category_data.xml',
        'security/ir.model.access.csv',
        'reports/sponsorships_evolution_reports_view.xml',
        'reports/end_sponsorships_report_view.xml',
        'reports/new_sponsorships_report_view.xml',
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
        'views/contract_view.xml',
        'views/postpone_waiting_reminder_wizard_view.xml',
        'views/correspondence_view.xml',
        'views/gift_compassion_view.xml',
        'views/load_csv_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
