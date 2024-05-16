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
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    @author: Roman Zoller, Emanuel Cino, Michaël Sandoz
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
    "name": "Sponsor to beneficiary email communication",
    "version": "12.0.2.0.0",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": [
        "partner_communication_switzerland",
        "child_switzerland",
        "sbc_translation",  # compassion-modules
    ],
    "external_dependencies": {
        "python": [
            "PyPDF2",
            "pysftp",
            "wand",
            "fitz",  # PyMuPDF
            "boxdetect",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "data/scan_letter_params.xml",
        "data/import_config_templates.xml",
        "data/nas_parameters.xml",
        "data/translator_email.xml",
        "data/communication_config.xml",
        "data/res.lang.compassion.csv",
        "views/import_config_view.xml",
        "views/import_letters_history_view.xml",
        "views/s2b_generator_view.xml",
        "reports/translation_reports_view.xml",
    ],
    "demo": [],
    "installable": True,
}
