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


def remove_old_views(cr):
    """ Remove old views to avoid errors. """
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = 'partner_compassion' "
        "AND model = 'ir.ui.view' ")
    view_ids = [str(row[0]) for row in cr.fetchall()]
    cr.execute(
        "DELETE FROM ir_ui_view "
        "WHERE inherit_id IN (%s) " % ','.join(view_ids))
    cr.execute(
        "DELETE FROM ir_ui_view "
        "WHERE id IN (%s) " % ','.join(view_ids))


def migrate(cr, version):
    if not version:
        return

    # Change type of analytic accounts
    remove_old_views(cr)
