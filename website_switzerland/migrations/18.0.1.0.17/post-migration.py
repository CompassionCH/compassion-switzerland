from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The group visit registrations wait in Trip paid: the person responsible
    moves them to Criminal record (T3523). The stages are noupdate."""
    env.ref("website_switzerland.stage_group_unconfirmed").manual_only = True
