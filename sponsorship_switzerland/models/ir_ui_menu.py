# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api
from odoo.tools.safe_eval import safe_eval


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.multi
    def get_needaction_data(self):
        res = super(IrUiMenu, self).get_needaction_data()

        waiting_menu = \
            self.env.ref('sponsorship_switzerland.menu_waiting_mandate')
        if waiting_menu.id in self.ids:
            domain = safe_eval(waiting_menu.action.domain)
            model = waiting_menu.action.res_model
            counter = \
                len(self.env[model].search(domain, limit=100, order='id DESC'))

            res[waiting_menu.id]['needaction_enabled'] = True
            res[waiting_menu.id]['needaction_counter'] = counter

        return res
