#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
from base64 import b64decode

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype


class SignOcaRequestPaper(models.TransientModel):
    _name = "sign.oca.request.paper"
    _description = "Sign request signed on paper"

    request_id = fields.Many2one("sign.oca.request", required=True, readonly=True)
    signer_ids = fields.Many2many(
        "sign.oca.request.signer",
        compute="_compute_signer_ids",
        string="Signers",
        help="Signers who have not signed online yet: the scan counts as their "
        "signature.",
    )
    data = fields.Binary("Signed scan", required=True, help="PDF of the signed paper.")
    filename = fields.Char()
    signed_on = fields.Datetime("Signed on", required=True, default=fields.Datetime.now)

    @api.depends("request_id")
    def _compute_signer_ids(self):
        for wizard in self:
            wizard.signer_ids = wizard.request_id.signer_ids.filtered(
                lambda s: not s.signed_on
            )

    def action_confirm(self):
        """The scan replaces the document of the request and every signer who
        has not signed yet is marked as signed, like an online signature: log,
        hash and inalterability sequence."""
        self.ensure_one()
        request = self.request_id
        request.check_access("write")
        if request.state not in ("1_draft", "0_sent"):
            raise UserError(
                self.env._("Only a draft or sent request can be signed on paper.")
            )
        signers = self.signer_ids
        if not signers:
            raise UserError(self.env._("Every signer has already signed."))
        pdf = b64decode(self.data)
        if guess_mimetype(pdf) != "application/pdf":
            raise UserError(self.env._("The signed scan must be a PDF file."))
        digest = hashlib.sha1(pdf).hexdigest()
        request = request.sudo()
        request.write(
            {
                "data": self.data,
                "filename": self.filename or request.filename,
                "current_hash": digest,
                # No e-mail: the signers already signed the paper
                "state": "0_sent",
            }
        )
        for signer in signers.sudo():
            signer.write({"signed_on": self.signed_on, "signature_hash": digest})
            signer._set_action_log("paper_sign")
            if signer.sequence_id:
                signer.flush_recordset()
                number = signer.sequence_id.next_by_id()
                signer.write(
                    {
                        "secure_sequence_number": number,
                        "inalterable_hash": signer._get_new_hash(number),
                    }
                )
        request.message_post(
            body=self.env._(
                "Signed on paper by %(signers)s, scan uploaded by %(user)s.",
                signers=", ".join(signers.mapped("partner_id.name")),
                user=self.env.user.name,
            ),
        )
        request._check_signed()
        request.action_send_signed_request()
        return {"type": "ir.actions.act_window_close"}
