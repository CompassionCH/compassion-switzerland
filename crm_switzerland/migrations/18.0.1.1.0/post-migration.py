import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Reconcile the Salesperson of each church with its CRM opportunities.

    For every church, fold all of its opportunities' salespeople (plus its
    own current salesperson) through the same arbitration logic used going
    forward (see res.partner.resolve_church_salesperson): archived
    candidates are discarded, Church Engagement department wins ties, and
    churches left without any valid candidate get a to-do activity for
    Daniel Müller instead of being changed.
    """
    churches = env["res.partner"].search([("is_church", "=", True)])
    reconciled = 0
    notified = 0
    for church in churches:
        leads = (
            env["crm.lead"]
            .with_context(active_test=False)
            .search([("partner_id", "=", church.id), ("user_id", "!=", False)])
        )
        if not leads:
            continue
        changed = False
        for lead in leads:
            new_salesperson, _notify = church.resolve_church_salesperson(lead.user_id)
            if new_salesperson:
                church.user_id = new_salesperson
                changed = True
        if changed:
            reconciled += 1
        if not church._is_church_salesperson_valid(church.user_id):
            church._notify_daniel_no_church_salesperson(
                context_note=(" (found while reconciling historical CRM/church data)")
            )
            notified += 1
    _logger.info(
        "Church salesperson reconciliation: %s churches updated, "
        "%s left without a valid salesperson (Daniel notified)",
        reconciled,
        notified,
    )
