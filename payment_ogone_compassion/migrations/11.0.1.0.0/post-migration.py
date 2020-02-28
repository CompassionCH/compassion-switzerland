from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # Update payment_acquirers
    env.cr.execute("""
        select id from ir_ui_view where name = 'ogone_acquirer_button'
    """)
    old_view_id = env.cr.fetchone()[0]
    new_view_id = env.ref('payment_ogone.ogone_form').id
    env['payment.acquirer'].search([
        ('view_template_id', '=', old_view_id)
    ]).write({'view_template_id': new_view_id})
