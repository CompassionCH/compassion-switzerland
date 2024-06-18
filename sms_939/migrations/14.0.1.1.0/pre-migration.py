def migrate(cr, version):
    cr.execute(
        """
        INSERT INTO sms_sms(create_date, partner_id, number, body, state)
        SELECT sms_log.date, partner_id, mobile, text, 'sent'
        FROM sms_log JOIN res_partner ON sms_log.partner_id = res_partner.id
    """
    )
