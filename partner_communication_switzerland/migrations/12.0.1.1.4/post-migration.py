import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, installed_version):
    if not installed_version:
        return

    # Add activities "for dont inform" sponsors
    sponsorships = env["res.partner"]\
        .search([('global_communication_delivery_preference', '=', 'none')])\
        .sponsorship_ids\
        .filtered(lambda it: it.state in ["waiting", 'active'])

    for sponsorship in sponsorships:
        # Add the activity
        sponsorship.notify_sds_new_sponsorship()
