from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    # Link existing communication rules to XML ids.
    rules_mapping = {
        "Sponsorship Onboarding - Sponsorship confirmation": (
            "config_onboarding_sponsorship_confirmation",
            "mail_onboarding_sponsorship_confirmation"),
        "Sponsorship Onboarding Step 1 - Child and Payment Info": (
            "config_onboarding_step1", "mail_onboarding_step1"),
        "Sponsorship Onboarding Step 2 - Video and Country Information": (
            "config_onboarding_step2", "mail_onboarding_step2"),
        "Sponsorship Onboarding Step 3 - Poverty and Child protection": (
            "config_onboarding_step3", "mail_onboarding_step3"),
        "Sponsorship Onboarding Step 4 - Letter information": (
            "config_onboarding_step4", "mail_onboarding_step4"),
        "Sponsorship Onboarding Step 5 - Feedback & Engagement": (
            "config_onboarding_step5", "mail_onboarding_step5"),
        "Sponsorship Onboarding - Photo by post": (
            "config_onboarding_photo_by_post", "mail_onboarding_photo_by_post"),
        "Sponsorship Onboarding - Zoom Reminder": (
            "config_onboarding_zoom_reminder", "mail_onboarding_zoom_reminder"),
    }
    module = "partner_communication_switzerland"
    for rule_name, rule_ids in rules_mapping.items():
        rule = env["partner.communication.config"].search([("name", "=", rule_name)])
        if not rule:
            continue
        openupgrade.add_xmlid(
            env.cr, module, rule_ids[0], "partner.communication.config", rule.id)
        openupgrade.add_xmlid(
            env.cr, module, rule_ids[1], "mail.template", rule.email_template_id.id)
    # Remove old communications without deleting it from database (to keep history)
    env.cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'partner_communication_switzerland'
        AND name IN (
            'planned_dossier', 'planned_welcome', 'welcome_activation',
            'sms_registration_confirmation_2'
        );
    """)
    # Update sds_state.
    env.cr.execute("""
    UPDATE recurring_contract
    SET sds_state = 'active'
    WHERE sds_state = 'waiting_welcome';
    """)
    # Delete old view
    env.cr.execute("""
    DELETE FROM ir_ui_view
    WHERE arch_db LIKE '%welcome_active_letter_sent%'
    """)
