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
from odoo import api, models


class CompassionChild(models.Model):
    _inherit = 'compassion.child'

    @api.multi
    def get_sms_sponsor_child_data(self):
        """
        Returns JSON data of the child for the mobile sponsor page
        :return: JSON data
        """
        result = super(CompassionChild, self).get_sms_sponsor_child_data()
        if self.env.lang == 'fr_CH':
            result['description'] = self.desc_fr
        elif self.env.lang == 'de_DE':
            result['description'] = self.desc_de
        elif self.env.lang == 'it_IT':
            result['description'] = self.desc_it
        return result
