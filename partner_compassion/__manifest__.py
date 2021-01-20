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
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
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
    "name": "Upgrade Partners for Compassion Suisse",
    "version": "12.0.1.1.1",
    "category": "Partner",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "base_location",  # oca_addons/partner-contact
        "geoengine_base_geolocalize",  # geospatialslac
        "account_banking_mandate",  # oca_addons/bank-payment
        "account_bank_statement_import_camt_details",
        "sbc_compassion",  # compassion-modules
        "thankyou_letters",  # compassion-modules
        "mail_tracking",
        "partner_contact_birthdate",  # oca_addons/partner-contact
        "web_notify",  # oca_addons/web
        "partner_contact_in_several_companies",  # oca_addons/partner-contact
        "crm_claim",
        "base_search_fuzzy",  # oca_addons/server-tools
        "cms_form_compassion",  # compassion-modules
        "survey",  # source/addons
        "base_phone",  # oca_addons/connector-telephony
        "auditlog",
        "l10n_ch_zip",  # oca_addon/l10n_switzerland
        "web_view_google_map"  # oca_addon/web_view_google_map
    ],
    "external_dependencies": {"python": ["pandas", "pyminizip", "magic"]},
    "data": [
        "security/ir.model.access.csv",
        "security/criminal_record_groups.xml",
        "data/partner_category_data.xml",
        "data/partner_title_data.xml",
        "data/advocate_engagement_data.xml",
        "data/calendar_event_type.xml",
        "data/ir_cron.xml",
        "data/mail_channel.xml",
        "data/res_partner_actions.xml",
        "data/gist_indexes.xml",
        "data/partner_action_rules.xml",
        "views/advocate_details.xml",
        'views/search_bank_address_wizard.xml',
        "views/survey_user_input_action.xml",
        "views/partner_compassion_view.xml",
        "views/product_view.xml",
        "views/partner_check_double.xml",
        "views/notification_settings_view.xml",
        "views/tag_merge_wizard_action.xml",
        "views/mail_mail.xml",
        "templates/child_protection_charter.xml",
    ],
    "qweb": ["static/src/xml/thread_custom.xml"],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
