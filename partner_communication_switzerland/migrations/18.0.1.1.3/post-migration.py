from odoo.tools.misc import file_open


def migrate(cr, version):
    """TT3391 Migration : FIX sponsorship reminders"""
    _dir = "partner_communication_switzerland/migrations/18.0.1.1.3"
    template_file = f"{_dir}/sponsorship_reminder_{{nb}}.html"
    # Sponsorship reminder number : database id
    template_ids = {1: 90, 2: 91, 3: 439}
    for nb, template_id in template_ids.items():
        with file_open(template_file.format(nb=nb)) as template_content:
            content = template_content.read()
            cr.execute(
                """
                UPDATE mail_template
                SET body_html = %s::jsonb
                WHERE id = %s;
            """,
                [content, template_id],
            )
