# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models

from ..tools.wp_sync import WPSync


class CompassionProject(models.Model):
    _inherit = 'compassion.project'

    def suspend_funds(self):
        """ Remove children from the website when FCP Suspension occurs. """
        children = self.env['compassion.child'].search([
            ('project_id', 'in', self.ids),
            ('state', '=', 'I')
        ])
        if children:
            wp_config = self.env['wordpress.configuration'].get_config()
            wp = WPSync(wp_config)
            wp.remove_children(children)
        return super(CompassionProject, self).suspend_funds()
