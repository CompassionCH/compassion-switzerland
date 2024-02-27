##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, api, exceptions, fields, models


class GenerateCommunicationWizard(models.TransientModel):
    _name = "partner.communication.test.cases.wizard"

    config_id = fields.Many2one(
        "partner.communication.config",
        string="Communication rule",
        default=lambda s: s.env.context.get("active_id"),
        required=True,
    )
    language = fields.Selection("_get_lang", default=lambda self: self.env.lang)
    partner = fields.Many2one("res.partner", string="Partner", required=False)
    partner_selected = fields.Boolean(compute="_compute_partner_selected", store=True)
    send_mode = fields.Selection(
        [("digital", _("By e-mail")), ("physical", _("Print report"))],
        default="digital",
    )
    child_ids = fields.Many2many("compassion.child", string="Selected children")
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

    @api.onchange("partner")
    def onchange_partner(self):
        if self.partner:
            self.child_ids = self.partner.mapped("sponsored_child_ids")

    @api.depends("partner")
    @api.multi
    def _compute_partner_selected(self):
        for line in self:
            if len(line.partner) <= 0:
                line.partner_selected = False
            else:
                line.partner_selected = line.partner.name != ""

    @api.multi
    def generate_test_cases_single(self):
        self.ensure_one()
        cases = self.config_id.generate_test_cases_by_language_family_case(
            self.language, "single", self.send_mode
        )
        self._apply_cases(cases)
        return True

    @api.multi
    def generate_test_cases_family(self):
        self.ensure_one()
        cases = self.config_id.generate_test_cases_by_language_family_case(
            self.language, "family", self.send_mode
        )
        self._apply_cases(cases)
        return True

    @api.multi
    def generate_test_cases_partner(self):
        self.ensure_one()
        if not self.partner_selected:
            raise exceptions.UserError("No partner selected")
        case = self.config_id.generate_test_case_by_partner(
            self.partner, self.child_ids, self.send_mode
        )
        self._apply_cases([case])
        return True

    def _apply_cases(self, cases):
        for case in cases:
            setattr(self, case["case"] + "_subject", case["subject"])
            setattr(self, case["case"] + "_body", case["body_html"])
