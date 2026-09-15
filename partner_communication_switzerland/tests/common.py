##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import io
import logging
import os
from unittest import mock
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from PIL import Image

from odoo import fields
from odoo.tools.config import config

_logger = logging.getLogger(__name__)


def setup_tour_admin(env):
    """Prepares the user the tours run as."""
    admin = env.ref("base.user_admin")
    admin.tour_enabled = False
    admin.groups_id |= env.ref("account.group_account_invoice")
    admin.lang = "en_US"

    actions = env.ref("sponsorship_compassion.upsert_partner") | env.ref(
        "sponsorship_compassion.create_sponsorship"
    )
    actions.auto_process = False
    return admin


def get_or_create_origin(env, name):
    """The 'other' sponsorship origin a tour selects, created on first run."""
    origin = env["recurring.contract.origin"].search(
        [("type", "=", "other"), ("other_name", "=", name)], limit=1
    )
    return origin or env["recurring.contract.origin"].create(
        {"type": "other", "other_name": name}
    )


def enable_connect_fake(test_class):
    previous = config.options.get("connect_fake")
    config.options["connect_fake"] = True
    test_class.addClassCleanup(config.options.__setitem__, "connect_fake", previous)


def check_queue_runs(env):
    if "queue.job" in env and not os.environ.get("QUEUE_JOB__NO_DELAY"):
        raise ValueError(
            "queue_job is installed: run the tour with QUEUE_JOB__NO_DELAY=1 "
            "so that the queued work of the tour is executed."
        )


def get_sponsorable_child(env, local_id):
    """The child of a tour, ready to be sponsored again."""
    child = env["compassion.child"].search([("local_id", "=", local_id)], limit=1)
    if not child:
        return create_consigned_child(env, local_id)
    if child.state != "N":
        reset_tour_data(env, child)
    return child


def reset_tour_data(env, child):
    """Puts back what a previous run of a tour consumed."""
    if not child:
        return
    sponsorships = env["recurring.contract"].search([("child_id", "in", child.ids)])
    _logger.info(
        "Releasing %s from %s sponsorship(s)", child.local_id, len(sponsorships)
    )
    with mock.patch.object(
        type(env["compassion.child"]), "get_lifecycle_event", return_value=[]
    ):
        sponsorships.with_context(force_delete=True).unlink()
        child.invalidate_recordset()
        if not child.hold_id:
            child.hold_id = _create_hold(env, "No Money Hold", child)
        if child.state != "N":
            child.child_unsponsored()
            child.invalidate_recordset()
    if child.state != "N":
        raise ValueError(
            f"The child {child.local_id} is still in state {child.state} and "
            "cannot be sponsored again by the tour."
        )


def create_consigned_child(env, local_id):
    """A child on a consignment hold, ready to be sponsored."""
    hold = _create_hold(env, "Consignment Hold")
    child = (
        env["compassion.child"]
        .with_context(no_upsert=True)
        .create(
            {
                "local_id": local_id,
                "global_id": uuid4().hex,
                "firstname": "Aylin",
                "preferred_name": "Aylin",
                "lastname": "Yilmaz",
                "state": "N",
                "birthdate": fields.Date.today() - relativedelta(years=8),
                "project_id": _create_project(env, local_id).id,
                "hold_id": hold.id,
            }
        )
    )
    hold.child_id = child
    _add_child_pictures(child)
    return child


def _create_hold(env, hold_type, child=None):
    """A hold of the given type, valid for long enough to run the tour."""
    return env["compassion.hold"].create(
        {
            "hold_id": uuid4().hex,
            "type": hold_type,
            "expiration_date": fields.Datetime.now() + relativedelta(weeks=2),
            "primary_owner": env.user.id,
            "child_id": child.id if child else False,
        }
    )


def _create_project(env, local_id):
    """Creates the project the child of the tour belongs to."""
    icp_details = env.ref("child_compassion.icp_details")
    auto_process = icp_details.auto_process
    icp_details.auto_process = False
    try:
        return env["compassion.project"].create(
            {"fcp_id": local_id[:5], "name": "Onboarding Tour Project"}
        )
    finally:
        icp_details.auto_process = auto_process


def _add_child_pictures(child):
    env = child.env
    picture = io.BytesIO()
    Image.new("RGB", (16, 16), "white").save(picture, "PNG")
    with mock.patch(
        "odoo.addons.child_compassion.models.child_pictures.urlopen",
        side_effect=lambda *args, **kwargs: io.BytesIO(picture.getvalue()),
    ):
        pictures = env["compassion.child.pictures"].create(
            {
                "child_id": child.id,
                "image_url": "https://media.ci.org/image/upload/v1/tour.jpg",
            }
        )
    if not pictures.fullshot:
        raise ValueError("The child of the tour needs a portrait")
