from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    # Link existing communication rules to XML ids.
    rules_mapping = {
        "MyAccount - New User": (
            "myaccount_welcome_config",
            "myaccount_welcome_email"),
    }
    module = "mobile_app_switzerland"
    for rule_name, rule_ids in rules_mapping.items():
        rule = env["partner.communication.config"].search([("name", "=", rule_name)])
        if not rule:
            continue
        openupgrade.add_xmlid(
            env.cr, module, rule_ids[0], "partner.communication.config", rule.id)
        openupgrade.add_xmlid(
            env.cr, module, rule_ids[1], "mail.template", rule.email_template_id.id)
