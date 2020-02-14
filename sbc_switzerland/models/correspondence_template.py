##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione <marco.mon@windowslive.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class CorrespondenceTemplate(models.Model):

    _inherit = 'correspondence.template'

    checkbox_ids = fields.Many2many(
        default=lambda self: self._get_default_checkboxes())

    def _get_default_checkboxes(self):
        return [
            (0, False, {'language_id': self.env.ref(
                'child_compassion.lang_compassion_french').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_german').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_italian').id}),
            (0, False, {'language_id': self.env.ref(
                'child_compassion.lang_compassion_english').id}),
            (0, False, {'language_id': self.env.ref(
                'child_compassion.lang_compassion_spanish').id}),
            (0, False, {'language_id': False}),
        ]
