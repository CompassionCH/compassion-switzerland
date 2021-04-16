##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class CompassionChildPictures(models.Model):
    """ Allows getting translated fields on the website """

    _name = "compassion.child.pictures"
    _inherit = ["compassion.child.pictures", "translatable.model"]
