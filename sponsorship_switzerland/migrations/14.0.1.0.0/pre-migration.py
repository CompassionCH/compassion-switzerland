from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_xmlids(
        cr,
        [
            (
                "sponsorship_compassion.product_template_sponsorship",
                "sponsorship_switzerland.product_template_sponsorship",
            ),
            (
                "sponsorship_compassion.product_template_sponsorship_ldp",
                "sponsorship_switzerland.product_template_sponsorship_ldp",
            ),
            (
                "sponsorship_compassion.product_template_fund_gen",
                "sponsorship_switzerland.product_template_fund_gen",
            ),
            (
                "sponsorship_compassion.product_template_gift_birthday",
                "sponsorship_switzerland.product_template_gift_birthday",
            ),
            (
                "sponsorship_compassion.product_template_gift_gen",
                "sponsorship_switzerland.product_template_gift_gen",
            ),
            (
                "sponsorship_compassion.product_template_gift_family",
                "sponsorship_switzerland.product_template_gift_family",
            ),
            (
                "sponsorship_compassion.product_template_gift_project",
                "sponsorship_switzerland.product_template_gift_project",
            ),
            (
                "sponsorship_compassion.product_template_gift_graduation",
                "sponsorship_switzerland.product_template_gift_graduation",
            ),
        ],
    )
    openupgrade.load_data(cr, "sponsorship_switzerland", "data/completion_rules.xml")
    openupgrade.load_data(cr, "account_statement_completion", "data/data.xml")
