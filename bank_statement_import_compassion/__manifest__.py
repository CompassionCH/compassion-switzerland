##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#
#    Copyright (C) 2016-2020 Compassion CH (http://www.compassion.ch)
#    @author: Jérémie Lang <jlang@compassion.ch>
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
    "name": "Compassion Bank Account Import",
    "version": "14.0.0.1.0",
    "category": "Account",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "author": "Jérémie Lang for Compassion CH",
    "license": "AGPL-3",
    "installable": True,
    "data": [
        "views/account_bank_statement_line.xml",
        "views/account_bank_statement_line_form.xml",
    ],
    "depends": [
        "base",
        "account_statement_import_base",
        "account_statement_import_camt",
        "account_statement_import_camt54",
        "account_reconciliation_widget",
    ],
}
