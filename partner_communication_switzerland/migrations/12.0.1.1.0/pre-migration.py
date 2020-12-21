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
    # Update data
    openupgrade.load_xml(
        env.cr, module, "/data/onboarding_process.xml"
    )
