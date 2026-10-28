##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The tax receipt waits for the donor's name. Its rule is noupdate data of
    partner_communication_switzerland: data/communication_config.xml only sets
    it on a new database."""
    config = env.ref(
        "partner_communication_switzerland.tax_receipt_config",
        raise_if_not_found=False,
    )
    if config:
        config.my2_wait_for_name = True
