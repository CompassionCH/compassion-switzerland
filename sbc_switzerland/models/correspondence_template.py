from odoo import models, api, fields


class CorrespondenceTemplate(models.Model):

    _inherit = 'correspondence.template'

    checkbox_ids = fields.One2many(
        'correspondence.lang.checkbox', 'template_id',
        default=lambda self: self._get_default_checkboxes(), copy=True)

    def _get_default_checkboxes(self):
        return [
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_french').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_german').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_italian').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_english').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_spanish').id}),
            (0, False, {'language_id': False}),
        ]

