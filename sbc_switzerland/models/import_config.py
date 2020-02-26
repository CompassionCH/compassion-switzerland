##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Michael Sandoz <sandozmichael@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class ImportConfig(models.Model):
    """ This class defines all metadata of a correspondence"""

    _inherit = 'import.letter.config'

    import_folder_path = fields.Char()

    def get_fields(self):
        res = super().get_fields()
        res.append('import_folder_path')
        return res
