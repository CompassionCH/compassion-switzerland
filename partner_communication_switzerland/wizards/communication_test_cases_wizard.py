##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields, _, exceptions


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
    partner = fields.Many2one(
        "res.partner", string="Partner",
        required=False
    )
    send_mode = fields.Selection(
        [("digital", _("By e-mail")),
         ("physical", _("Print report"))],
        default="digital"
    )
    single_1_child_subject = fields.Char(readonly=True)
    single_3_child_subject = fields.Char(readonly=True)
    single_4_child_subject = fields.Char(readonly=True)
    family_1_child_subject = fields.Char(readonly=True)
    family_3_child_subject = fields.Char(readonly=True)
    family_4_child_subject = fields.Char(readonly=True)

    single_1_child_body = fields.Html(readonly=True)
    single_3_child_body = fields.Html(readonly=True)
    single_4_child_body = fields.Html(readonly=True)
    family_1_child_body = fields.Html(readonly=True)
    family_3_child_body = fields.Html(readonly=True)
    family_4_child_body = fields.Html(readonly=True)

    partner_subject = fields.Html(readonly=True)
    partner_body = fields.Html(readonly=True)

    def _compute_display_name(self):
        for wizard in self:
            wizard.display_name = "Test cases"

    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]


    @api.multi
    def generate_test_cases_single(self):
        self.ensure_one()
        cases = self.config_id.generate_test_cases_by_language_family_case(
            self.language, "single", self.send_mode)
        self._apply_cases(cases)
        return True

    @api.multi
    def generate_test_cases_family(self):
        self.ensure_one()
        cases = self.config_id.generate_test_cases_by_language_family_case(
            self.language, "family", self.send_mode)
        self._apply_cases(cases)
        return True

    @api.multi
    def generate_test_cases_partner(self):
        self.ensure_one()
        if len(self.partner) < 1:
            raise exceptions.UserError("No partner selected")
            return False
        case = self.config_id.generate_test_case_by_partner(self.partner, self.send_mode)
        self._apply_cases([case])
        return True

    @api.multi
    def generate_test_cases_all(self):
        self.ensure_one()
        answer = True
        answer &= self.generate_test_cases_single()
        answer &= self.generate_test_cases_family()
        answer &= self.generate_test_cases_partner()
        return answer


    def _apply_cases(self, cases):
        for case in cases:
            setattr(self, case["case"] + "_subject", case["subject"])
            setattr(self, case["case"] + "_body", case["body_html"])
