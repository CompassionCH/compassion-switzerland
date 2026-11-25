import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

QR_RULES = (
    "sponsorship_switzerland.reconcile_model_qr_funds",
    "sponsorship_switzerland.reconcile_model_qr_gifts",
)


def setup_qr_rules(env):
    """T3622 The automatic invoice matching rule (rule 25, database only)
    reconciles a QR payment only with the open items of exactly its QR
    reference and amount. The QR reference rules come right after it, on the
    same journals. The order of the other rules is kept."""
    model_obj = env["account.reconcile.model"]
    invoice_rule = model_obj.search(
        [
            ("company_id", "=", env.ref("base.main_company").id),
            ("rule_type", "=", "invoice_matching"),
            ("auto_reconcile", "=", True),
            ("match_text_location_reference", "=", True),
        ],
        order="sequence, id",
        limit=1,
    )
    if not invoice_rule:
        _logger.warning("T3622 no invoice matching rule found, QR rules unchanged")
        return
    invoice_rule.write({"match_exact_reference": True, "exact_amount_only": True})
    qr_rules = model_obj.browse([env.ref(xmlid).id for xmlid in QR_RULES])
    # Make room after the invoice matching rule
    following = model_obj.search(
        [
            ("company_id", "=", invoice_rule.company_id.id),
            ("id", "not in", qr_rules.ids),
            "|",
            ("sequence", ">", invoice_rule.sequence),
            "&",
            ("sequence", "=", invoice_rule.sequence),
            ("id", ">", invoice_rule.id),
        ]
    )
    for rule in following:
        rule.sequence += len(qr_rules)
    for position, rule in enumerate(qr_rules, start=1):
        rule.write(
            {
                "sequence": invoice_rule.sequence + position,
                "match_journal_ids": [(6, 0, invoice_rule.match_journal_ids.ids)],
            }
        )
    _logger.info(
        "T3622 exact QR reference and amount on rule %s, QR rules %s after it",
        invoice_rule.id,
        qr_rules.ids,
    )


@openupgrade.migrate()
def migrate(env, version):
    setup_qr_rules(env)
