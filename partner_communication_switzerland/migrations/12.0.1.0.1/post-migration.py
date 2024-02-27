from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return
    openupgrade.load_xml(
        cr, "partner_communication_switzerland", "report/child_picture.xml"
    )
