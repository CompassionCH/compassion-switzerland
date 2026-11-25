from openupgradelib import openupgrade

MODULE = "partner_communication_switzerland"

# 18.0.1.1.13 linked cc_church_inspiration to the config since renamed
# "App Access" in production; Church Inspiration was then created again.
RECORDS = {
    "cc_app_access": "Compassion Communities - App Access",
    "cc_church_inspiration": "Compassion Communities - Church Inspiration",
}


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    for key, name in RECORDS.items():
        cr.execute(
            """
            SELECT c.id, c.email_template_id FROM partner_communication_config c
            JOIN utm_source s ON s.id = c.source_id
            WHERE s.name ILIKE %s
            """,
            (name,),
        )
        rows = cr.fetchall()
        if len(rows) != 1:
            openupgrade.logger.warning(
                "Expected one config named '%s', found %s: %s not linked.",
                name,
                len(rows),
                key,
            )
            continue
        config_id, template_id = rows[0]
        _set_xmlid(cr, f"{key}_rule", "partner.communication.config", config_id)
        if template_id:
            _set_xmlid(cr, f"{key}_template", "mail.template", template_id)
    # The App Access email must not carry the payment slips.
    cr.execute(
        """
        UPDATE partner_communication_config c SET attachments_function = NULL
        FROM ir_model_data d
        WHERE d.module = %s AND d.name = 'cc_app_access_rule' AND d.res_id = c.id
        """,
        (MODULE,),
    )


def _set_xmlid(cr, xmlid, model, res_id):
    cr.execute(
        "UPDATE ir_model_data SET res_id = %s WHERE module = %s AND name = %s",
        (res_id, MODULE, xmlid),
    )
    if not cr.rowcount:
        openupgrade.add_xmlid(cr, MODULE, xmlid, model, res_id, noupdate=True)
