##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ChildOnWorpressWizard(models.TransientModel):
    _name = 'child.on.wordpress.wizard'
    _description = "Put children on WordPress"

    child_ids = fields.Many2many(
        'compassion.child', compute='_compute_active_ids',
        string='Selected children', default=lambda c: c._compute_active_ids()
    )

    def _compute_active_ids(self):
        children = self.env['compassion.child'].browse(
            self.env.context.get('active_ids'))
        possible_states = ['N', 'R', 'Z']
        valid_children = children.filtered(
            lambda c: c.state in possible_states)
        for wizard in self:
            wizard.child_ids = valid_children
        return valid_children

    @api.multi
    def put_child_on_internet(self):
        res = self.child_ids.add_to_wordpress()

        if not res:
            raise UserError(_("Child upload failed."))
        else:
            return True
