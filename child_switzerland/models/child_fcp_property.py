from odoo import models, fields


class TranslateProperty(models.AbstractModel):
    _name = "compassion.translate.property"
    _description = "Compassion translate property"

    value = fields.Char("English value")
    value_fr = fields.Char(
        "French value", compute="_compute_value_fr", inverse="_inverse_value_fr"
    )
    value_it = fields.Char(
        "Italian value", compute="_compute_value_it", inverse="_inverse_value_it"
    )
    value_de = fields.Char(
        "German value", compute="_compute_value_de", inverse="_inverse_value_de"
    )

    def _compute_value_fr(self):
        for property in self:
            property.value_fr = property.with_context(lang="fr_CH").value

    def _inverse_value_fr(self):
        for property in self:
            property.with_context(lang="fr_CH").value = property.value_fr

    def _compute_value_it(self):
        for property in self:
            property.value_it = property.with_context(lang="it_IT").value

    def _inverse_value_it(self):
        for property in self:
            property.with_context(lang="it_IT").value = property.value_it

    def _compute_value_de(self):
        for property in self:
            property.value_de = property.with_context(lang="de_DE").value

    def _inverse_value_de(self):
        for property in self:
            property.with_context(lang="de_DE").value = property.value_de


class FcpProperty(models.AbstractModel):
    _inherit = ["fcp.property", "compassion.translate.property"]
    _name = "fcp.property"


class ChildProperty(models.AbstractModel):
    _inherit = ["child.property", "compassion.translate.property"]
    _name = "child.property"
