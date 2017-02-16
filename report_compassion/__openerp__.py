# -*- encoding: utf-8 -*-
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
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
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


{
    'name': 'Compassion CH PDF-Qweb Reports',
    'version': '8.0.1.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['sponsorship_switzerland', 'l10n_ch_payment_slip'],
    'data': [
        'security/ir.model.access.csv',
        'data/success_story_activation_cron.xml',
        'report/compassion_layout.xml',
        'report/paperformats.xml',
        'report/childpack.xml',
        'report/bvr_layout.xml',
        'report/bvr_sponsorship.xml',
        'report/partner_communication.xml',
        'report/sub_proposal_form.xml',
        'report/bvr_gift.xml',
        'report/anniversary_card.xml',
        'report/a4_bvr.xml',
        'views/print_sponsorship_bvr_view.xml',
        'views/print_sponsorship_gift_bvr_view.xml',
        'views/print_childpack_view.xml',
        'views/success_story_view.xml',
        'views/communication_job_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
