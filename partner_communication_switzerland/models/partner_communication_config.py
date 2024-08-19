##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import random

from odoo import api, fields, models


class PartnerCommunication(models.Model):
    _inherit = "partner.communication.config"

    product_id = fields.Many2one(
        "product.product",
        "Fund Bill attachment",
        domain=[("categ_id.name", "=", "Fund")],
    )

    @api.onchange("product_id")
    def onchange_product(self):
        if self.product_id:
            self.attachments_function = "get_fund_bvr"

    def generate_test_cases_by_language_family_case(
        self, lang="de_DE", family_case="single", send_mode="digital"
    ):
        """
        Generates example communications for our multiple cases in CH
        depending on the language and the family case
        Outputs the texts in a file
        :param lang:
        :return: True
        """
        self.ensure_one()

        comm_obj = self.env["partner.communication.job"].with_context(
            must_skip_send_to_printer=True
        )

        res = []

        for number_sponsorship in [1, 3, 4]:
            partner = self._find_partner(number_sponsorship, lang, family_case)
            if partner is None:
                continue
            object_ids = self._get_test_objects(partner)
            object_ids = ",".join([str(id) for id in object_ids[0:number_sponsorship]])
            temp_comm = comm_obj.create(
                {
                    "partner_id": partner.id,
                    "config_id": self.id,
                    "object_ids": object_ids,
                    "auto_send": False,
                    "send_mode": send_mode,
                }
            )
            res.append(
                {
                    "case": f"{family_case}_{number_sponsorship}_child",
                    "subject": temp_comm.subject,
                    "body_html": temp_comm.body_html,
                }
            )
            temp_comm.unlink()

        return res

    def generate_test_case_by_partner(self, partner, children, send_mode):
        """
        Generates example communications for our multiple cases in CH
        depending on partner
        Outputs the texts in a file
        """
        self.ensure_one()

        comm_obj = self.env["partner.communication.job"].with_context(
            must_skip_send_to_printer=True
        )
        object_ids = self._get_test_objects(partner, children)
        object_ids = ",".join([str(id) for id in object_ids])
        temp_comm = comm_obj.create(
            {
                "partner_id": partner.id,
                "config_id": self.id,
                "object_ids": object_ids,
                "auto_send": False,
                "send_mode": send_mode,
            }
        )
        res = {
            "case": "partner",
            "subject": temp_comm.subject,
            "body_html": temp_comm.body_html,
        }
        temp_comm.unlink()

        return res

    def open_test_case_wizard(self):
        return {
            "name": "Test communication cases",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "context": self.env.context,
            "res_model": "partner.communication.test.cases.wizard",
            "target": "current",
        }

    def _get_test_objects(self, partner, children=None):
        object_ids = []
        if self.model == "res.partner":
            object_ids = partner.ids
        elif self.model == "recurring.contract":
            sponsorships = partner.sponsorship_ids
            if children:
                sponsorships = sponsorships.filtered(lambda s: s.child_id in children)
            object_ids = sponsorships.ids
        elif self.model == "correspondence":
            letters = partner.mapped("sponsorship_ids.child_letter_ids")
            if children:
                letters = letters.filtered(lambda letter: letter.child_id in children)
            object_ids = letters.ids
        elif self.model == "compassion.child":
            selected_children = children or partner.sponsored_child_ids
            object_ids = selected_children.ids
        elif self.model == "account.move.line":
            object_ids = (
                self.env["account.move.line"]
                .search(
                    [
                        # Don't restrict to a specific partner as a partner
                        # might not have any line.
                        ("move_id.invoice_category", "=", "fund"),
                    ],
                    limit=4,
                )
                .ids
            )
        elif self.model == "account.move":
            object_ids = (
                self.env["account.move"]
                .search([("partner_id", "=", partner.id)], limit=4)
                .ids
            )
        elif self.model == "res.partner.zoom.session":
            object_ids = (
                self.env["res.partner.zoom.session"]
                .search([("participant_ids.partner_id", "=", partner.id)], limit=2)
                .ids
            )
        return object_ids

    def _find_partner(self, number_sponsorships, lang, family_case):
        family = self.env.ref("partner_compassion.res_partner_title_family")

        query = [
            ("number_sponsorships", "=", number_sponsorships),
            ("lang", "=", lang),
        ]
        if family_case == "single":
            query += [("title", "!=", family.id), ("title.plural", "=", False)]
        else:
            query += [("title", "=", family.id)]
        if self.model == "res.partner.zoom.session":
            zoom_participants = (
                self.env["res.partner.zoom.attendee"]
                .search([], limit=80)
                .mapped("partner_id")
                .ids
            )
            query += [("id", "in", zoom_participants)]

        answers = self.env["res.partner"].search(query, limit=50)

        # check that the query returned a result
        if len(answers) <= 0:
            return None

        # randomly select one
        answer = random.choice(answers)
        return answer
