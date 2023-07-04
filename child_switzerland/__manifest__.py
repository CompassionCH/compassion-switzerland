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
#    Copyright (C) 2016-2020 Compassion CH (http://www.compassion.ch)
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
    "name": "Compassion CH Children",
    "version": "14.0.1.0.0",
    "category": "Compassion",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://www.compassion.ch",
    "external_dependencies": {"python": ["pypng", "pyqrcode"]},
    "depends": [
        "child_compassion",  # compassion-modules
        "report_wkhtmltopdf_param",  # OCA/reporting-engine
    ],
    "data": [
        "data/ir.advanced.translation.csv",
        "data/res.lang.compassion.csv",
        "report/childpack.xml",
        "views/description_views.xml",
        "views/res_country_view.xml",
        "views/child_or_fcp_property_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
