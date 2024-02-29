from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Update existing communication rules linked to old invoice model
    env["partner.communication.config"].search(
        [("model_id.model", "=", "account.invoice")]
    ).write({"model_id": env.ref("account.model_account_move").id})
    env["partner.communication.config"].search(
        [("model_id.model", "=", "account.invoice.line")]
    ).write({"model_id": env.ref("account.model_account_move_line").id})
