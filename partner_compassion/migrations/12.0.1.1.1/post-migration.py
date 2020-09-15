from openupgradelib import openupgrade

magazine_number_mapping = [
    (-1, "email"),
    (0, "no_mag"),
    (1, "one"),
    (2, "two"),
    (3, "three"),
    (4, "four"),
    (5, "five"),
    (6, "six"),
    (7, "seven"),
    (8, "eight"),
    (9, "nine"),
    (10, "ten"),
    (15, "fifteen"),
    (20, "twenty"),
    (25, "twenty_five"),
    (50, "fifty"),
]


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    openupgrade.map_values(
        env.cr,
        "nbmag_moved0",
        "nbmag",
        magazine_number_mapping,
        table="res_partner"
    )
    openupgrade.drop_columns(
        env.cr,
        [("res_partner", "nbmag_moved0")]
    )
