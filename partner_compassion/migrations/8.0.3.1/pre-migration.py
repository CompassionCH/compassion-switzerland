# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
logger = logging.getLogger()


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
    UPDATE res_partner SET thankyou_letter = 'default' WHERE thankyou_letter =
        'email';
    UPDATE res_partner SET tax_certificate = 'default' WHERE tax_certificate =
        'email';
    """)
