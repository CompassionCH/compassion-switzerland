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

    # Move views that were in module muskathlon
    openupgrade.rename_xmlids(env.cr, [
        ('muskathlon.modal_form', 'website_compassion.modal_form'),
        ('muskathlon.modal_form_buttons',
         'website_compassion.modal_form_buttons'),
        ('muskathlon.field_widget_hidden',
         'website_compassion.field_widget_hidden'),
        ('muskathlon.field_widget_gtc', 'website_compassion.field_widget_gtc'),
        ('muskathlon.widget_payment', 'website_compassion.widget_payment'),
        ('muskathlon.payment_submit', 'website_compassion.payment_submit'),
    ])
