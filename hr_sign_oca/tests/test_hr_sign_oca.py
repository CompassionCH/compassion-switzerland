import base64

from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, new_test_user
from odoo.tools import file_open

from odoo.addons.base.tests.common import BaseCommon


class TestHrSignOca(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with file_open("sign_oca/tests/empty.pdf", "rb") as f:
            cls.pdf = f.read()
        cls.scan = cls.pdf.replace(b"%%EOF", b"% scanned paper\n%%EOF")
        cls.role = cls.env["sign.oca.role"].create(
            {
                "name": "Employee",
                "partner_selection_policy": "expression",
                "expression_partner": "{{object.work_contact_id.id}}",
            }
        )
        cls.template = cls.env["sign.oca.template"].create(
            {
                "name": "Staff regulations",
                "data": base64.b64encode(cls.pdf),
                "filename": "regulations.pdf",
                "model_id": cls.env.ref("hr.model_hr_employee").id,
            }
        )
        cls.template.add_item(
            {
                "field_id": cls.env.ref("sign_oca.sign_field_name").id,
                "role_id": cls.role.id,
                "page": 1,
                "position_x": 10,
                "position_y": 10,
                "width": 10,
                "height": 10,
                "required": True,
            }
        )
        cls.employee_user = new_test_user(
            cls.env, login="hr_sign_employee", groups="base.group_user"
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Signing Employee", "user_id": cls.employee_user.id}
        )
        cls.hr_user = new_test_user(
            cls.env,
            login="hr_sign_manager",
            groups="base.group_user,hr.group_hr_user,sign_oca.sign_oca_group_manager",
        )
        cls.sign_user = new_test_user(
            cls.env,
            login="hr_sign_own",
            groups="base.group_user,sign_oca.sign_oca_group_user",
        )

    def _generate(self):
        wizard = Form(
            self.env["sign.oca.template.generate.multi"].with_context(
                model="hr.employee", active_ids=self.employee.ids
            )
        )
        wizard.template_id = self.template
        action = wizard.save().generate()
        return self.env["sign.oca.request"].search(action["domain"])

    def _paper_wizard(self, request, data=None, user=None):
        env = self.env(user=user or self.hr_user)
        return env["sign.oca.request.paper"].create(
            {
                "request_id": request.id,
                "data": base64.b64encode(data or self.scan),
                "filename": "scan.pdf",
                "signed_on": "2026-11-20 10:00:00",
            }
        )

    def _employee_documents(self):
        return self.env["ir.attachment"].search(
            [("res_model", "=", "hr.employee"), ("res_id", "=", self.employee.id)]
        )

    def test_request_linked_to_employee(self):
        request = self._generate()
        self.assertEqual(request.employee_id, self.employee)
        self.assertEqual(request.signer_ids.partner_id, self.employee.work_contact_id)
        self.assertEqual(self.employee.sign_request_count, 1)
        action = self.employee.action_view_sign_requests()
        self.assertEqual(self.env["sign.oca.request"].search(action["domain"]), request)

    def test_signed_on_paper(self):
        request = self._generate()
        signer = request.signer_ids
        self.assertEqual(request.state, "0_sent")
        self.assertFalse(self._employee_documents())
        wizard = self._paper_wizard(request)
        self.assertEqual(wizard.signer_ids, signer)
        wizard.action_confirm()

        self.assertEqual(request.state, "2_signed")
        self.assertEqual(base64.b64decode(request.data), self.scan)
        self.assertEqual(request.filename, "scan.pdf")
        self.assertEqual(str(signer.signed_on), "2026-11-20 10:00:00")
        self.assertTrue(signer.signature_hash)
        self.assertTrue(signer.secure_sequence_number)
        self.assertFalse(signer.altered_hash)
        log = self.env["sign.oca.request.log"].search(
            [("request_id", "=", request.id), ("action", "=", "paper_sign")]
        )
        self.assertEqual(log.signer_id, signer)
        self.assertEqual(log.uid, self.hr_user)
        self.assertIn("Signed on paper", request.message_ids[0].body)
        document = self._employee_documents()
        self.assertEqual(document.name, "Staff regulations - Signing Employee.pdf")
        self.assertEqual(document.raw, self.scan)
        self.assertIn(document, self.employee.message_ids.attachment_ids)

    def test_draft_request_signed_on_paper_without_mail(self):
        request = self.env["sign.oca.request"].create(
            self.template._prepare_sign_oca_request_vals_from_record(self.employee)
        )
        self.assertEqual(request.state, "1_draft")
        mails = self.env["mail.mail"].search_count([])
        self._paper_wizard(request).action_confirm()
        self.assertEqual(request.state, "2_signed")
        self.assertEqual(self.env["mail.mail"].search_count([]), mails)

    def test_signed_online_document_on_employee(self):
        request = self._generate()
        signer = request.signer_ids
        info = signer.with_user(self.employee_user).sudo().get_info()
        data = {
            key: dict(item, value="Signing Employee")
            for key, item in info["items"].items()
        }
        # Like the portal controller: the employee, through sudo
        signer.with_user(self.employee_user).sudo().action_sign(data)
        self.assertEqual(request.state, "2_signed")
        document = self._employee_documents()
        self.assertEqual(document.datas, request.data)
        self.assertEqual(self.employee.message_ids[0].attachment_ids, document)

    def test_scan_must_be_pdf(self):
        request = self._generate()
        with self.assertRaisesRegex(UserError, "PDF"):
            self._paper_wizard(
                request, data=b"\x89PNG\r\n\x1a\n" + b"0" * 32
            ).action_confirm()
        self.assertEqual(request.state, "0_sent")
        self.assertFalse(request.signer_ids.signed_on)

    def test_signed_or_cancelled_request_refused(self):
        request = self._generate()
        self._paper_wizard(request).action_confirm()
        with self.assertRaisesRegex(UserError, "draft or sent"):
            self._paper_wizard(request).action_confirm()
        other = self._generate()
        other.cancel()
        with self.assertRaisesRegex(UserError, "draft or sent"):
            self._paper_wizard(other).action_confirm()

    def test_only_sign_managers(self):
        request = self._generate()
        with self.assertRaises(AccessError):
            self._paper_wizard(request, user=self.sign_user)
        with self.assertRaises(AccessError):
            self._paper_wizard(request, user=self.employee_user)
