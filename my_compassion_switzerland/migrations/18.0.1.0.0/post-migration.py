##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def _reactivate_module_views(env):
    """Reactivate this module's views.

    The migrated database carries them deactivated (the module was dormant
    during the database migration) and a module update never touches the
    active flag; without this the website templates and backend views
    resolve as "not found".
    """
    view_refs = env["ir.model.data"].search(
        [
            ("module", "=", "my_compassion_switzerland"),
            ("model", "=", "ir.ui.view"),
        ]
    )
    views = env["ir.ui.view"].browse(view_refs.mapped("res_id")).exists()
    for view in views.filtered(lambda view: not view.active):
        # A view dropped from the manifest is still present at this point
        # (records are garbage-collected after the migration scripts) and
        # may no longer validate; leave it deactivated for the cleanup.
        try:
            with env.cr.savepoint():
                view.write({"active": True})
            _logger.info("reactivated view %s", view.key or view.name)
        except ValidationError:
            _logger.warning(
                "left view %s deactivated, it no longer validates",
                view.key or view.name,
            )


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _reactivate_module_views(env)

    _logger.info("reloading Volunteer Registration mail template with QWeb body")
    openupgrade.load_data(
        env, "my_compassion_switzerland", "data/mail_template_data.xml"
    )
