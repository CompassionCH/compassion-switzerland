from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    categ_gif = env.ref("sponsorship_compassion.product_category_gift")
    products = env["product.template"].search([("categ_id", "=", categ_gif.id)])
    for product in products:
        code = product.default_code.replace("gift_", "")
        gift_type = env.ref(
            f"sponsorship_compassion.gift_type_{code}", raise_if_not_found=False
        )
        if gift_type:
            product.sponsorship_gift_type_id = gift_type
    christmas = env.ref("sponsorship_switzerland.product_template_fund_nol")
    christmas.sponsorship_gift_type_id = env.ref(
        "sponsorship_compassion.gift_type_christmas"
    )
