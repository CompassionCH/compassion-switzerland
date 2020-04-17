from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return

    # Associate already created toilets fund to new xml record
    toilets_fund = env["product.template"].search(
        [("name", "=", "Toilets for all - 2019")]
    )

    if toilets_fund:
        openupgrade.add_xmlid(
            cr,
            "sponsorship_switzerland",
            "product_template_fund_toilets",
            "product.template",
            toilets_fund.id,
        )
