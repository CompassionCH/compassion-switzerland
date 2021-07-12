##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields, _


class GenerateCommunicationWizard(models.TransientModel):
    _name = "partner.communication.test.cases.wizard"

    config_id = fields.Many2one(
        "partner.communication.config", string="Communication rule",
        default=lambda s: s.env.context.get("active_id"),
        required=True
    )
    language = fields.Selection(
        "_get_lang", default=lambda self: self.env.lang
    )
    send_mode = fields.Selection(
        [("digital", _("By e-mail")),
         ("physical", _("Print report"))],
        default="digital"
    )
    single_1_child_subject = fields.Char(readonly=True)
    single_3_children_subject = fields.Char(readonly=True)
    single_4_children_subject = fields.Char(readonly=True)
    family_1_child_subject = fields.Char(readonly=True)
    family_3_children_subject = fields.Char(readonly=True)
    family_4_children_subject = fields.Char(readonly=True)

    single_1_child_body = fields.Html(readonly=True)
    single_3_children_body = fields.Html(readonly=True)
    single_4_children_body = fields.Html(readonly=True)
    family_1_child_body = fields.Html(readonly=True)
    family_3_children_body = fields.Html(readonly=True)
    family_4_children_body = fields.Html(readonly=True)

    def _compute_display_name(self):
        for wizard in self:
            wizard.display_name = "Test cases"

    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]

    @api.multi
    def generate_test_cases(self):
        self.ensure_one()
        for data in self.config_id.generate_test_cases(self.language, self.send_mode):
            setattr(self, data["case"] + "_subject", data["subject"])
            setattr(self, data["case"] + "_body", data["body_html"])
        return True
