##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def create(self, vals_list):
        """No need to update mailchimp from res_users"""
        return super(ResUsers, self.with_context(no_need=True)).create(vals_list)

    def write(self, vals):
        """No need to update mailchimp from res_users"""
        return super(ResUsers, self.with_context(no_need=True)).write(vals)
