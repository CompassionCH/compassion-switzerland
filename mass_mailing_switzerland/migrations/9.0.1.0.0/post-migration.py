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

    # Change old domains of mailings and delete test mailings
    cr.execute("""
        update mail_mass_mailing
        set mailing_domain = replace(
          mailing_model,
          'property_payment_term.name',
          'customer_payment_mode_id.name')
        where mailing_domain like '%property_payment_term.name%';

        update mail_mass_mailing
        set mailing_domain = '[]'
        where mailing_domain = 'res.partner';

        delete from mail_mass_mailing
        where state = 'test';
    """)
