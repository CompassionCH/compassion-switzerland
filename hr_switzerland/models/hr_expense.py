# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class HrExpense(models.Model):
    _inherit = "hr.expense"

    # Make product editable when expense is submitted
    product_id = fields.Many2one(
        states={
            'draft': [('readonly', False)],
            'submit': [('readonly', False)]
        }
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Prevent changing amounts if expense is submitted.
        """
        if self.state == 'draft':
            super(HrExpense, self)._onchange_product_id()


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    # Adding a user_id field for the assign notification to work
    user_id = fields.Many2one(related='employee_id.user_id')

    @api.model
    def create(self, vals):
        """Notify managers when expense is created."""
        sheet = super(HrExpenseSheet, self).create(vals)
        users = sheet._get_users_to_subscribe() - self.env.user
        sheet._message_auto_subscribe_notify(users.mapped('partner_id').ids)
        return sheet

    def _add_followers(self):
        """Notify managers when employee is changed."""
        super(HrExpenseSheet, self)._add_followers()
        users = self._get_users_to_subscribe() - self.env.user
        self._message_auto_subscribe_notify(users.mapped('partner_id').ids)
