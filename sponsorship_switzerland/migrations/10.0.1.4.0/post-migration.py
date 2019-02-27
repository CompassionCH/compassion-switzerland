# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import datetime


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
ALTER TABLE recurring_contract 
ADD COLUMN mandate_date timestamp without time zone;
UPDATE recurring_contract SET mandate_date = %s WHERE state = 'mandate';
    """ % str(datetime.now()))
