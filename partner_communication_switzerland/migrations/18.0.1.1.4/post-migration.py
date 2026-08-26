def migrate(cr, version):
    """TT3391 Migration : FIX wordpress_form_data in mail templates"""
    cr.execute(
        """
UPDATE mail_template
SET body_html = replace(body_html::text, '?{{partner.wordpress_form_data}}', '')::jsonb
WHERE id IN (303, 77, 80);
UPDATE mail_template
SET body_html = replace(
        body_html::text, '?{{object.partner_id.wordpress_form_data}}', '')::jsonb
WHERE id = 85;
UPDATE mail_template
SET body_html = replace(
    body_html::text,
    '?{{partner.with_context(mailchimp_child=child).wordpress_form_data}}', '')::jsonb
WHERE id = 66;
UPDATE mail_template
SET body_html = replace(
        body_html::text, '?<t t-out=\"partner.wordpress_form_data\"></t>', '')::jsonb
WHERE id = 77;
UPDATE mail_template
SET body_html = replace(
    body_html::text,
'?<t t-out=\"partner.with_context(mailchimp_child=child).wordpress_form_data\"></t>',
    '')::jsonb
WHERE id = 132;
    """
    )
