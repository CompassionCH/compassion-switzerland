from openupgradelib import openupgrade

MODULE = "partner_communication_switzerland"

# Records created by hand in the database, matched by name to the new XML ids.
# The XML ids must exist before the data file is loaded, otherwise the records
# would be created a second time.
RECORDS = {
    "cc_welcome": "Compassion Communities - Welcome and payment information",
    "cc_payment_request": "Compassion Communities - Payment request",
    "cc_church_inspiration": "Compassion Communities - Church inspiration",
    "cc_tax_receipt": "Compassion Communities - Tax receipt",
    "cc_annual_impact_report": "Compassion Communities - Annual impact report",
    "cc_virtual_connection_invitation": (
        "Compassion Communities - Virtual connection invitation"
    ),
    "cc_virtual_connection": "Compassion Communities - Virtual connection",
    "cc_call_to_continue": "Compassion Communities - Call to continue",
    "cc_call_to_continue_yes": "Compassion Communities - Call to continue yes",
    "cc_call_to_continue_no": "Compassion Communities - Call to continue no",
    "cc_no_sub": "Sponsorship - No SUB - Compassion Communities",
}
OLD_XMLIDS = [
    "m2m_welcome_rule",
    "m2m_welcome_template",
    "m2m_stop_rule",
    "m2m_stop_template",
]


@openupgrade.migrate()
def migrate(env, version):
    """Link the existing Compassion Communities communications to the new XML ids
    and retire the Many2Many ones, which are replaced."""
    cr = env.cr
    for key, name in RECORDS.items():
        cr.execute(
            """
            SELECT c.id FROM partner_communication_config c
            JOIN utm_source s ON s.id = c.source_id
            WHERE s.name = %s
            """,
            (name,),
        )
        _add_xmlid(
            cr, f"{key}_rule", "partner.communication.config", name, cr.fetchall()
        )
        cr.execute("SELECT id FROM mail_template WHERE name->>'en_US' = %s", (name,))
        _add_xmlid(cr, f"{key}_template", "mail.template", name, cr.fetchall())
    _retire_many2many(cr)


def _add_xmlid(cr, xmlid, model, name, rows):
    if len(rows) != 1:
        openupgrade.logger.warning(
            "Expected one %s named '%s', found %s: %s not linked.",
            model,
            name,
            len(rows),
            xmlid,
        )
        return
    openupgrade.add_xmlid(cr, MODULE, xmlid, model, rows[0][0], noupdate=True)


def _retire_many2many(cr):
    """The old records stay in the database for the history of the sent
    communications: archive the rules and drop the XML ids."""
    cr.execute(
        """
        UPDATE partner_communication_config c SET active = false
        FROM utm_source s
        WHERE s.id = c.source_id AND s.name LIKE 'Many2Many Onboarding%'
        """
    )
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = %s AND name IN %s",
        (MODULE, tuple(OLD_XMLIDS)),
    )
