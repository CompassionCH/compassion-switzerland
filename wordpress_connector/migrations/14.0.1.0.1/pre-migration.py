from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.add_xmlid(
        cr,
        "wordpress_connector",
        "wordpress_configuration",
        "wordpress.configuration",
        2,
    )
