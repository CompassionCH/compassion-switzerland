##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class PartnerCommunication(models.Model):
    _inherit = "partner.communication.config"

    @api.multi
    def generate_test_cases(self, lang="de_DE", send_mode="digital"):
        """
        Generates example communications for our multiple cases in CH.
        Outputs the texts in a file
        :param lang:
        :return: True
        """
        self.ensure_one()
        family = self.env.ref("partner_compassion.res_partner_title_family")
        # Find a partner with > 3 sponsorships
        family_partner = self.env["res.partner"].search([
            ("number_sponsorships", ">", 3),
            ("lang", "=", lang),
            ("title", "=", family.id)
        ], limit=1)
        single_partner = self.env["res.partner"].search([
            ("number_sponsorships", ">", 3),
            ("lang", "=", lang),
            ("title", "!=", family.id),
            ("title.plural", "=", False)
        ], limit=1)
        comm_obj = self.env["partner.communication.job"].with_context(must_skip_send_to_printer=True)
        res = []
        for partner in (single_partner + family_partner):
            if self.model == "res.partner":
                object_ids = partner.ids
            elif self.model == "recurring.contract":
                object_ids = partner.sponsorship_ids.ids
            elif self.model == "correspondence":
                object_ids = partner.mapped("sponsorship_ids.child_letter_ids").ids
            elif self.model == "compassion.child":
                object_ids = partner.sponsored_child_ids.ids
            elif self.model == "account.invoice.line":
                object_ids = self.env["account.invoice.line"].search([
                    ("partner_id", "=", partner.id),
                    ("invoice_id.invoice_category", "=", "fund")
                ], limit=4).ids
            temp_comm = comm_obj.create({
                "partner_id": partner.id,
                "config_id": self.id,
                "object_ids": object_ids,
                "auto_send": False,
                "send_mode": send_mode,
            })
            case = "single" if partner == single_partner else "family"
            res.append({
                "case": f"{case}_4_children",
                "subject": temp_comm.subject,
                "body_html": temp_comm.body_html})
            temp_comm.object_ids = ",".join(map(str, object_ids[:3]))
            temp_comm.refresh_text()
            res.append({
                "case": f"{case}_3_children",
                "subject": temp_comm.subject,
                "body_html": temp_comm.body_html})
            temp_comm.object_ids = object_ids[0]
            temp_comm.refresh_text()
            res.append({
                "case": f"{case}_1_child",
                "subject": temp_comm.subject,
                "body_html": temp_comm.body_html})
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
            'target': 'current',
        }
