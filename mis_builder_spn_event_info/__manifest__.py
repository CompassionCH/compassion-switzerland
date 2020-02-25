# Copyright 2018-2020 Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    'name': 'MIS Builder event & sponsorship info',
    'summary': "Events, acquisition for MIS Builder",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'compassion suisse',
    'website': 'http://www.compassion.ch',
    'depends': [
        'mis_builder',  # OCA/mis_builder
        'crm_compassion',  # compassion-modules
        'account',  # source
        'website_event_compassion'  # compassion-switzerland
    ],
    'data': [
        'security/mis_spn_event_info.xml',
        'views/mis_spn_event_info.xml',
    ],
    'installable': True,
    'maintainers': ['davidwul'],
}
