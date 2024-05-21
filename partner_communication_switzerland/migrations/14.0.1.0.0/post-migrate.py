from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Update existing communication rules linked to old invoice model
    move_config = env["partner.communication.config"].search(
        [("model_id.model", "=", "account.invoice")]
    )
    move_config.write({"model_id": env.ref("account.model_account_move").id})

    move_line_config = env["partner.communication.config"].search(
        [("model_id.model", "=", "account.invoice.line")]
    )
    move_line_config.write({"model_id": env.ref("account.model_account_move_line").id})

    move_comms = env["partner.communication.job"].search(
        [("config_id", "in", move_config.ids)]
    )
    update_object_ids(env, move_comms, "account_move", "old_invoice_id")

    move_line_comms = env["partner.communication.job"].search(
        [("config_id", "in", move_line_config.ids)]
    )
    update_object_ids(env, move_line_comms, "account_move_line", "old_invoice_line_id")

    env.cr.execute(
        """
            UPDATE mail_template
            SET body_html = REPLACE(REPLACE(body_html, 'invoice_id', 'move_id'),
                                    'account.invoice', 'account.move');
            UPDATE ir_translation
            SET value = REPLACE(REPLACE(value, 'invoice_id', 'move_id'),
                                'account.invoice', 'account.move')
            WHERE name LIKE '%body_html' AND value LIKE '%invoice%';
        """
    )


def update_object_ids(env, comms, table, old_id_field):
    for comm in comms.filtered("object_ids"):
        ids = map(int, comm.object_ids.split(","))
        env.cr.execute(
            f"SELECT id FROM {table} WHERE {old_id_field} IN %s", (tuple(ids),)
        )
        new_ids = [r[0] for r in env.cr.fetchall()]
        if new_ids:
            comm.write({"object_ids": new_ids})
