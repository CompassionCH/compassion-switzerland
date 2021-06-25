from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    missing_partners = env["mail.mass_mailing.contact"].search([
        ("partner_ids", "=", False),
    ])
    for contact in missing_partners:
        partners = env["res.partner"].search([
            ("email", "=", contact.email),
            ("contact_type", "=", "standalone")
        ])
        contact.partner_id = partners[:1]
        contact.participant_ids = partners
