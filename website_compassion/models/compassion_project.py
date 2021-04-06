##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class CompassionProject(models.Model):
    _inherit = "compassion.project"

    supported_types = ["cognitive", "physical", "socio", "spiritual"]

    def get_activity_for_age(self, age, type="physical"):
        if type and type not in self.supported_types:
            raise ValueError(f"Type {type} is not supported."
                             f"It should be in {self.supported_types}")
        if age < 0:
            raise ValueError("Age needs to be positive")
        elif age <= 5:
            return eval(f"self.{type}_activity_babies_ids")
        elif age <= 11:
            return eval(f"self.{type}_activity_kids_ids")
        else:
            return eval(f"self.{type}_activity_ados_ids")
