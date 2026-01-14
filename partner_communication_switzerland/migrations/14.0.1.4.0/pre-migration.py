from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    m2m_welcome_rule = env["partner.communication.config"].search(
        [
            (
                "email_template_id.name",
                "=",
                "Many2Many Onboarding - Welcome and payment information",
            )
        ]
    )
    m2m_stop_rule = env["partner.communication.config"].search(
        [
            (
                "email_template_id.name",
                "=",
                "Many2Many Onboarding - Stop recurrent donation",
            )
        ]
    )
    if m2m_welcome_rule:
        openupgrade.add_xmlid(
            env.cr,
            "partner_communication_switzerland",
            "m2m_welcome_rule",
            "partner.communication.config",
            m2m_welcome_rule.id,
            True,
        )
        openupgrade.add_xmlid(
            env.cr,
            "partner_communication_switzerland",
            "m2m_welcome_template",
            "mail.template",
            m2m_welcome_rule.email_template_id.id,
            True,
        )
    if m2m_stop_rule:
        openupgrade.add_xmlid(
            env.cr,
            "partner_communication_switzerland",
            "m2m_stop_rule",
            "partner.communication.config",
            m2m_stop_rule.id,
            True,
        )
        openupgrade.add_xmlid(
            env.cr,
            "partner_communication_switzerland",
            "m2m_stop_template",
            "mail.template",
            m2m_stop_rule.email_template_id.id,
            True,
        )
