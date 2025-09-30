##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#
#    Copyright (C) 2016-2025 Compassion CH (http://www.compassion.ch)
#    @author: Dylan Bossoku <dbossoku@compassion.ch>
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
{
    "name": "Website Analytics",
    "summary": "This module allows you to integrate Google "
    "Analytics data into Odoo and display graphs",
    "author": "Compassion Switzerland",
    "version": "14.0.1.0.0",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "category": "Analytics",
    "license": "AGPL-3",
    "depends": ["child_compassion","mass_mailing"],
    "data": [
        "views/view_google_analytics_data_line_graph.xml",
        "actions/action_google_analytics_data_line_graph.xml",
        "views/view_google_analytics_kanban.xml",
        "views/view_google_analytics_tree.xml",
        "views/view_google_analytics_form.xml",
        "actions/action_google_analytics_report.xml",
        "menus/google_analytics_menus.xml",
        "data/website_analytics_config.xml",
        "security/google_analytics_security.xml",
        "security/ir.model.access.csv",
    ],
}
