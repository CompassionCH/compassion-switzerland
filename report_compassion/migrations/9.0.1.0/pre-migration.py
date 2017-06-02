# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Move data
    cr.execute("""
UPDATE ir_model_data SET module='partner_communication_switzerland'
WHERE module='thankyou_letters'
AND (name = 'event_letter_template' OR name LIKE 'config_event%');
    """)
