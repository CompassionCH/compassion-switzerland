from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Move xmls out of partner_communication_switzerland
    openupgrade.rename_xmlids(cr, [
        ("partner_communication_switzerland.ambassador_donation_confirmation_template",
         "muskathlon.ambassador_donation_confirmation_template"),
        ("partner_communication_switzerland.ambassador_donation_confirmation_config",
         "muskathlon.ambassador_donation_confirmation_config"),
    ])
