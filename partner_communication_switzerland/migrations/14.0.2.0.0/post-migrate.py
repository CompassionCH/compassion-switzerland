from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE mail_template
        SET body_html = REPLACE(body_html, 'public_url', 'get_start_url()')
        WHERE body_html like '%public_url%';
        """,
    )
