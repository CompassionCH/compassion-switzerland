##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from pypdf import PdfReader
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .common import create_consigned_child


def photos_pdf(codes):
    """A photos PDF like the biennial's: one 10x15 page per child, with the
    child code printed on it."""
    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=(101 * mm, 153 * mm))
    for code in codes:
        canvas.drawString(10 * mm, 20 * mm, f"Aylin {code}")
        canvas.showPage()
    canvas.save()
    return buffer.getvalue()


@tagged("post_install", "-at_install")
class TestBiennialPhotosZip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.children = create_consigned_child(
            cls.env, "ZZ9980001"
        ) | create_consigned_child(cls.env, "ZZ9980002")
        cls.sponsor = cls.env["res.partner"].create({"name": "Biennial Sponsor"})
        cls.biennial = cls.env.ref("partner_communication_compassion.biennial")

    def _biennial(self, codes):
        """The biennial of the two children, with a photos PDF of codes."""
        job = self.env["partner.communication.job"].create(
            {
                "config_id": self.biennial.id,
                "partner_id": self.sponsor.id,
                "object_ids": ",".join(map(str, self.children.ids)),
                "send_mode": "physical",
            }
        )
        job.attachment_ids.unlink()
        self.env["partner.communication.attachment"].create(
            {
                "name": "pictures.pdf",
                "communication_id": job.id,
                "report_name": "child_compassion.child_picture",
                "data": base64.b64encode(photos_pdf(codes)),
            }
        )
        return job

    def _zip(self, action):
        attachment_id = int(action["url"].split("/")[3].split("?")[0])
        attachment = self.env["ir.attachment"].browse(attachment_id)
        return ZipFile(BytesIO(attachment.raw))

    def test_one_pdf_per_child(self):
        """Each child's page, found by its code whatever the page order."""
        job = self._biennial(["ZZ9980002", "ZZ9980001"])
        self.assertTrue(job.is_biennial)
        archive = self._zip(job.action_download_photos_zip())
        names = sorted(archive.namelist())
        self.assertEqual(len(names), 2)
        for name, code in zip(names, ["ZZ9980001", "ZZ9980002"], strict=True):
            self.assertTrue(name.endswith(f"_{code}.pdf"), name)
            pdf = PdfReader(BytesIO(archive.read(name)))
            self.assertEqual(len(pdf.pages), 1)
            self.assertIn(code, pdf.pages[0].extract_text())

    def test_downloading_again_replaces_the_zip(self):
        job = self._biennial(["ZZ9980001", "ZZ9980002"])
        job.action_download_photos_zip()
        job.action_download_photos_zip()
        zips = self.env["ir.attachment"].search(
            [
                ("res_model", "=", job._name),
                ("res_id", "=", job.id),
                ("mimetype", "=", "application/zip"),
            ]
        )
        self.assertEqual(len(zips), 1)
        self.assertNotIn(zips, job.ir_attachment_ids, "never sent with the e-mail")

    def _rendered(self, codes):
        """The photos PDF the report would make now (tests render no PDF)."""
        return patch.object(
            type(self.env["partner.communication.job"]),
            "_get_pdf_from_data",
            lambda job, data, report: base64.b64encode(photos_pdf(codes)),
        )

    def test_photos_not_matching_the_children_are_made_again(self):
        """A PDF made before the communication changed, or none (sent by
        post): the photos are made again."""
        for codes in (["ZZ9980001"], []):
            job = self._biennial(codes)
            with self._rendered(["ZZ9980001", "ZZ9980002"]):
                archive = self._zip(job.action_download_photos_zip())
            self.assertEqual(len(archive.namelist()), 2)

    def test_photos_that_cannot_be_found(self):
        job = self._biennial(["ZZ9980001"])
        with self._rendered(["ZZ9980001"]), self.assertRaises(UserError):
            job.action_download_photos_zip()

    def test_from_the_action_menu_without_send_mode(self):
        """A biennial of a sponsor who gets no photo (no send mode): the
        Action menu runs without saving the form, which would refuse it."""
        job = self._biennial(["ZZ9980001", "ZZ9980002"])
        job.send_mode = False
        action = (
            self.env.ref("partner_communication_switzerland.download_photos_zip_action")
            .with_context(active_model=job._name, active_ids=job.ids, active_id=job.id)
            .run()
        )
        self.assertEqual(len(self._zip(action).namelist()), 2)

    def test_only_for_biennials(self):
        job = self._biennial(["ZZ9980001", "ZZ9980002"])
        job.config_id = self.env.ref("partner_communication.default_communication")
        self.assertFalse(job.is_biennial)
        with self.assertRaises(UserError):
            job.action_download_photos_zip()
