from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.logged_query(
        cr,
        """
UPDATE ir_model_data
SET name = REPLACE(name, '_ir_actions_server', '_action')
WHERE module = 'partner_communication_switzerland' AND name LIKE '%_ir_actions_server';
        """,
    )
    openupgrade.logged_query(
        cr,
        """
                             UPDATE mail_template
SET email_from = REPLACE(email_from, 'address_name', 'commercial_name')
WHERE email_from LIKE '%address_name%';
                             """,
    )
