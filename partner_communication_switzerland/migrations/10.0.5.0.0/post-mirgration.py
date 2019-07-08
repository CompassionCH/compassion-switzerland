# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return
    env.cr.execute("""
        UPDATE correspondence
        SET email_read = subquery.min
        FROM (SELECT correspondence.id, min(mail_tracking_event.time)
            FROM correspondence, mail_mail,
                mail_tracking_event, mail_tracking_email
        WHERE email_read_moved0
            AND email_id = mail_mail.id
            AND mail_mail.id = mail_tracking_email.mail_id
            AND mail_tracking_email.id = mail_tracking_event.tracking_email_id
            AND event_type = 'open'
            GROUP BY correspondence.id
            ) AS subquery
        WHERE correspondence.id = subquery.id;
    """)
