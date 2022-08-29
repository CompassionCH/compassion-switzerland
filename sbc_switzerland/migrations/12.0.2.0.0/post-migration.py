from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    translators = env["advocate.details"].search([
        ("engagement_ids", "=", 2),
    ])
    ts_user_obj = env["translation.user"]
    for translator in translators:
        partner = translator.partner_id
        user = env["res.users"].search([
            "|", ("partner_id", "=", partner.id), ("login", "=", partner.email),
            ("active", "in", [True, False])
        ], limit=1)
        if not user:
            # TODO Create a specific communication to warn the translator about the new account
            user = env["res.users"].create({
                "partner_id": partner.id,
                "login": partner.email or partner.ref
            })
        if not ts_user_obj.search([("user_id", "=", user.id), ("active", "in", [True, False])]):
            new_t = ts_user_obj.create([{
                "user_id": user.id,
                "translator_since": translator.active_since or translator.create_date,
                "active": not translator.state == "inactive"
            }])
            letters = env["correspondence"].search([
                ("translator_id", "=", partner.id)
            ])
            letters.write({"new_translator_id": new_t.id})
            for competence in letters.mapped("translation_competence_id"):
                env["translation.user.skill"].create([{
                    "translator_id": new_t.id,
                    "competence_id": competence.id,
                    "verified": True
                }])

    # Migrate letters already translated
    env.cr.execute("UPDATE correspondence SET translation_status = 'done' WHERE new_translator_id IS NOT NULL")

    # Migrate letters in translation
    letters = env["correspondence"].search([("state", "=", "Global Partner translation queue")])
    for l in letters:
        l.send_local_translate()
