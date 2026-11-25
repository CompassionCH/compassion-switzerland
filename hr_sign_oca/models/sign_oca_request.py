#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    employee_id = fields.Many2one(
        "hr.employee",
        compute="_compute_employee_id",
        store=True,
        index="btree_not_null",
        readonly=True,
    )

    @api.depends("record_ref")
    def _compute_employee_id(self):
        for request in self:
            record = request.record_ref
            request.employee_id = (
                record if record and record._name == "hr.employee" else False
            )

    def _check_signed(self):
        was_signed = self.state == "2_signed"
        res = super()._check_signed()
        if not was_signed and self.state == "2_signed":
            self._attach_signed_document_to_employee()
        return res

    def _attach_signed_document_to_employee(self):
        """Copy of the signed PDF in the chatter of the employee, where HR finds
        it without going through Sign. Runs as the signer (an employee without
        access to the employee records), hence sudo."""
        self.ensure_one()
        employee = self.sudo().employee_id
        if not employee:
            return
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": f"{self.name} - {employee.name}.pdf",
                    "datas": self.data,
                    "mimetype": "application/pdf",
                    "res_model": "hr.employee",
                    "res_id": employee.id,
                }
            )
        )
        employee.message_post(
            body=self.env._("Signed document: %s", self.name),
            attachment_ids=attachment.ids,
        )


class SignOcaRequestLog(models.Model):
    _inherit = "sign.oca.request.log"

    action = fields.Selection(
        selection_add=[("paper_sign", "Signed on paper")],
        ondelete={"paper_sign": lambda logs: logs.write({"action": "sign"})},
    )
