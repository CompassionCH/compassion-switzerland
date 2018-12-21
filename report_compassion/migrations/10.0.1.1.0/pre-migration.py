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


def migrate(cr, version):
    if not version:
        return

    openupgrade.add_xmlid(
        cr, 'report_compassion', 'communication_style_mailing_bvr',
        'ir.ui.view', 6928
    )
    openupgrade.add_xmlid(
        cr, 'report_compassion', 'partner_communication_document_mailing_bvr',
        'ir.ui.view', 6927
    )
    openupgrade.add_xmlid(
        cr, 'report_compassion', 'partner_communication_mailing_bvr',
        'ir.ui.view', 6926
    )
    openupgrade.add_xmlid(
        cr, 'report_compassion', 'report_partner_communication_mailing_bvr',
        'ir.actions.report.xml', 1458
    )
