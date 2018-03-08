# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade

import re


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    mail_tracking_events = env['mail.tracking.event'].search([
        ('url', '!=', False)
    ])

    p = re.compile(r'\/r\/([a-zA-Z0-9]{3,6})')

    for mail_tracking_event in mail_tracking_events:
        code = p.findall(mail_tracking_event.url)

        if code:
            link = env['link.tracker.code'].search([('code', '=', code[-1])])

            mail_tracking_event.url = link.link_id.url
