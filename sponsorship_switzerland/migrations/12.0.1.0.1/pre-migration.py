from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Associate already created toilets fund to new xml record
    toilets_fund = env["product.template"].search([("default_code", "=", "toilet")])

    if toilets_fund:
        openupgrade.add_xmlid(
            env.cr,
            "sponsorship_switzerland",
            "product_template_fund_toilets",
            "product.template",
            toilets_fund.id,
        )
