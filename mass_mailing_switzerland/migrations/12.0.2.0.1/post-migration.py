import logging
from openupgradelib import openupgrade


_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return
    # Attach main contacts to mailing contacts
    contacts = env["mail.mass_mailing.contact"].search([
        ("partner_id.contact_type", "=", "attached")
    ])
    count = 1
    to_update = []
    for contact in contacts:
        _logger.info("Migrating %s/%s contacts", count, len(contacts))
        if contact.partner_id.contact_id.email == contact.email:
            contact.partner_id = contact.partner_id.contact_id
            to_update.append(contact.partner_id.id)
            _logger.info("...Linked contact changed!")
        count += 1
    contacts.launch_job_update_mailchimp(to_update)
    _logger.info("Migration finished: updated %s contacts", len(to_update))
