# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    group_visit_configs = env['partner.communication.config'].search([
        ('name', 'ilike', 'Group visit')
    ])
    if group_visit_configs:
        # We hardcode the ids from production database
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_step1_config',
            'partner.communication.config', 88
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_step2_config',
            'partner.communication.config', 89
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_step3_config',
            'partner.communication.config', 90
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_medical_survey_config',
            'partner.communication.config', 91
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_travel_documents_config',
            'partner.communication.config', 92
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_information_day_config',
            'partner.communication.config', 93
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_detailed_config',
            'partner.communication.config', 94
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_before_sharing_config',
            'partner.communication.config', 95
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_after_trip_feedback_config',
            'partner.communication.config', 96
        )

        # Email templates
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_step1_email',
            'mail.template', 145
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_step2_email',
            'mail.template', 146
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion', 'group_visit_step3_email',
            'mail.template', 147
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_medical_survey_email',
            'mail.template', 148
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_travel_documents_email',
            'mail.template', 149
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_information_day_email',
            'mail.template', 150
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_detailed_info_email',
            'mail.template', 151
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_before_sharing_email',
            'mail.template', 152
        )
        openupgrade.add_xmlid(
            env.cr, 'website_event_compassion',
            'group_visit_after_trip_feedback_email',
            'mail.template', 153
        )
