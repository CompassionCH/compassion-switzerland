from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return

    openupgrade.load_xml(cr, 'partner_communication_switzerland',
                         'data/sponsorship_communications_cron.xml')
