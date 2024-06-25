from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.load_data(
        cr, "website_switzerland", "data/event_registration_stage.xml"
    )
    openupgrade.load_data(cr, "website_switzerland", "data/event_registration_task.xml")
    # Old unconfirmed stage is not used anymore
    cr.execute("DELETE FROM event_registration_stage WHERE id=1")
