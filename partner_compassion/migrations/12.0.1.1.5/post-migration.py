from openupgradelib.openupgrade import migrate


@migrate()
def update_res_partner_title_for_companies(env, installed_version):
    if not installed_version:
        return
    title = env.ref(
        "partner_compassion.res_partner_title_friends"
    ).id
    companies = env["res.partner"].search([
        ("is_company", "=", True), ("title", "!=", title)
    ])
    companies.write({"title": title})
