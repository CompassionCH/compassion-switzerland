##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields
from odoo.modules import module
import os


class PrintChildpack(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """
    _inherit = "print.childpack"

    type = fields.Selection(selection_add=[('child_switzerland.childpack_mini', 'Mini Childpack')])

    def _compute_module_name(self):
        super()._compute_module_name()
        if self.type == 'child_switzerland.childpack_mini':
            self.module_name = __name__.split('.')[2]
