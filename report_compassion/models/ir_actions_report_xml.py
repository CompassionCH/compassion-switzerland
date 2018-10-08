# -*- coding: utf-8 -*-
# Copyright (c) 2018 Emanuel Cino <ecino@compassion.ch>

from odoo import models, api


class IrActionsReportXml(models.Model):

    _inherit = 'ir.actions.report.xml'

    @api.multi
    def behaviour(self):
        """
        Change behaviour to return user preference in priority.
        :return: report action for printing.
        """
        result = super(IrActionsReportXml, self).behaviour()

        # Retrieve user default values
        user = self.env.user
        if user.printing_action:
            default_action = user.printing_action
            for key, val in result.iteritems():
                result[key]['action'] = default_action
        if user.printing_printer_id:
            default_printer = user.printing_printer_id
            for key, val in result.iteritems():
                result[key]['printer'] = default_printer
        return result
