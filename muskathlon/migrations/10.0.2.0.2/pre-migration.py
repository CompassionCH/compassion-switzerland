# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    xml_ids = [
        'cancel_transaction', 'cancel_transaction_on_update',
        'confirm_transaction', 'cancel_transaction_rule_time',
        'cancel_transaction_rule_update', 'confirm_transaction_rule'
    ]
    openupgrade.rename_xmlids(cr, [
        ('muskathlon.' + xml_id, 'cms_form_compassion.' + xml_id)
        for xml_id in xml_ids
    ])
