from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Associate already created toilets fund to new xml record
    covid_fund = env["product.template"].search([("default_code", "=", "coronavirus")])

    if covid_fund:
        openupgrade.add_xmlid(
            env.cr,
            "sponsorship_switzerland",
            "product_template_covid",
            "product.template",
            covid_fund.id,
        )
