import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, installed_version):
    if not installed_version:
        return

    # Generate all missing biennials since bug introduced by CS-428
    env.cr.execute(
        """
        select c.id
from compassion_child_pictures p join compassion_child c on p.child_id = c.id
where p.create_date > '2021-08-02 12:00:00' and c.sponsor_id is not null
order by p.create_date asc
    """
    )
    children = env["compassion.child"].browse([r[0] for r in env.cr.fetchall()])
    _logger.info("Generating missing biennials for %s children", len(children))
    comm_obj = env["partner.communication.job"]
    count = 0
    for child in children:
        count += 1
        existing = comm_obj.search_count(
            [
                ("config_id", "=", 36),  # Biennial config
                ("partner_id", "=", child.sponsor_id.id),
                ("date", ">=", "2021-08-02"),
                ("object_ids", "like", child.id),
            ]
        )
        if not existing:
            # This will trigger the biennial communication and the order photo
            child.new_photo()
        _logger.info("... %s / %s done", count, len(children))
