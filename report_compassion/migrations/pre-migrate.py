from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.add_xmlid(
        cr, "report_compassion", "new_donors_card_report", "ir.actions.report", 2069
    )
