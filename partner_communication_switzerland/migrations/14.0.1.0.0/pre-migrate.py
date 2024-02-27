from openupgradelib import openupgrade

swiss_to_compassion_xmlids = [
    "new_letter",
    "mail_onboarding_first_letter",
    "b2s_email_not_read",
    "child_letter_config",
    "child_letter_final_config",
    "child_letter_old_config",
    "config_onboarding_first_letter",
    "child_letter_unread",
    "major_revision_birthdate",
    "major_revision_disability",
    "major_revision_illness",
    "major_revision_name",
    "major_revision_gender",
    "major_revision_completion_date_change",
    "major_revision_parent_alive",
    "major_revision_caregiver",
    "major_revision_multiple",
    "lifecycle_child_transfer",
    "lifecycle_child_transition",
    "lifecycle_child_reinstatement",
    "project_suspension",
    "project_suspension_e1",
    "project_suspension_e2",
    "project_reactivation",
    "project_transition",
    "planned_dossier",
    "sponsorship_cancellation",
    "biennial",
    "child_notes",
    "disaster_alert",
    "new_dossier_transfer",
    "email_planned_exit_notification",
    "email_child_planned_exit",
    "email_child_unplanned_exit",
    "planned_exit_notification",
    "lifecycle_child_planned_exit",
    "lifecycle_child_unplanned_exit",
    "email_sponsorship_dossier",
    "email_child_transfer",
    "email_sponsorship_transfer_dossier",
    "email_child_transition",
    "email_child_reinstatement",
    "email_sponsorship_cancellation",
    "email_birthdate",
    "email_disability",
    "email_illness",
    "email_name",
    "email_gender",
    "email_completion_date_change",
    "email_parent_alive",
    "email_caregiver_change",
    "email_multiple_changes",
    "email_hold_removal",
    "email_biennial",
    "email_child_notes",
    "email_disaster_alert",
    "email_project_suspension",
    "email_project_suspension_e1",
    "email_project_suspension_e2",
    "email_project_reactivation",
    "email_project_transition",
    "utm_campaign_communication",
    "hold_removal",
]
swiss_to_reminder_xmlids = [
    "sponsorship_reminders_cron",
    "sponsorship_reminder_1",
    "sponsorship_reminder_2",
    "sponsorship_reminder_3",
    "sponsorship_activation_reminder_1",
    "sponsorship_activation_reminder_2",
    "sponsorship_activation_reminder_3",
    "email_sponsorship_reminder_1",
    "email_sponsorship_reminder_2",
    "email_sponsorship_reminder_3",
    "email_sponsorship_activation_reminder_1",
    "email_sponsorship_activation_reminder_2",
    "email_sponsorship_activation_reminder_3",
]


@openupgrade.migrate()
def migrate(env, version):
    # Merge and clean the communication records that were moved in
    # partner_communication_compassion
    swiss_module = "partner_communication_switzerland"
    comm_module = "partner_communication_compassion"
    reminder_module = "partner_communication_reminder"
    openupgrade.delete_records_safely_by_xml_id(
        env, [f"{comm_module}.{x}" for x in swiss_to_compassion_xmlids]
    )
    openupgrade.delete_records_safely_by_xml_id(
        env, [f"{reminder_module}.{x}" for x in swiss_to_reminder_xmlids]
    )
    for xmlid in swiss_to_compassion_xmlids:
        _update_ir_model_data(env.cr, swiss_module, comm_module, xmlid)
    for xmlid in swiss_to_reminder_xmlids:
        _update_ir_model_data(env.cr, swiss_module, reminder_module, xmlid)


def _update_ir_model_data(cr, old_module, new_module, xmlid):
    openupgrade.logged_query(
        cr,
        """DELETE FROM ir_model_data WHERE module=%s AND name=%s""",
        (new_module, xmlid),
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_model_data
        SET module=%s
        WHERE module=%s AND name=%s
        """,
        (new_module, old_module, xmlid),
    )
