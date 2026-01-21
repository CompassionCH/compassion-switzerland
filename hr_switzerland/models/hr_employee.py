##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class HrEmployee(models.AbstractModel):
    _inherit = "hr.employee.base"

    job_title = fields.Char(translate=True)
