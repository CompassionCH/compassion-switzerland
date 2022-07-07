from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return

    openupgrade.add_xmlid(
        cr, "partner_communication_switzerland", "wrpr_contribution_reminder_mail", "mail.template", 242)
    openupgrade.add_xmlid(
        cr, "partner_communication_switzerland", "wrpr_contribution_reminder_config",
        "partner.communication.config", 127)
