from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE mail_template
        SET body_html = REPLACE(body_html, 'public_url', 'get_start_url()')
        WHERE body_html LIKE '%public_url%';
        UPDATE ir_translation
        SET src = REPLACE(src, 'public_url', 'get_start_url()'),
            value = REPLACE(value, 'public_url', 'get_start_url()')
        WHERE res_id IN (SELECT id FROM mail_template WHERE body_html LIKE '%get_start_url()%')
        AND name='mail.template,body_html';
        """,
    )
