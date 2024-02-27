##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from base64 import b64decode

import mock

from odoo import fields
from odoo.tools import file_open

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

logger = logging.getLogger(__name__)

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)
mock_get_pdf = (
    "odoo.addons.base_report_to_printer."
    "models.ir_actions_report.IrActionsReport.render_qweb_pdf"
)

mock_release_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.release_hold"
)
mock_get_infos = (
    "odoo.addons.child_compassion.models.child_compassion" ".CompassionChild.get_infos"
)
mock_invoicer = (
    "odoo.addons.recurring_contract.models.contract_group"
    ".ContractGroup.generate_invoices"
)
mock_cleaner = (
    "odoo.addons.recurring_contract.models.recurring_contract"
    ".RecurringContract.clean_invoices"
)
mock_lifecycle = (
    "odoo.addons.child_compassion.models.child_compassion"
    ".CompassionChild.get_lifecycle_event"
)

mock_new_dossier = (
    "odoo.addons.partner_communication_switzerland.models"
    ".contracts.RecurringContract._new_dossier"
)


class TestSponsorship(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()
        # Deactivate mandates of Michel Fletcher to avoid directly validate
        # sponsorship to waiting state.
        self.michel.ref = self.ref(7)

        payment_mode_lsv = self.env.ref("sponsorship_switzerland.payment_mode_lsv")
        self.sp_group = self.create_group(
            {
                "partner_id": self.michel.id,
                "payment_mode_id": payment_mode_lsv.id,
            }
        )

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_co_1272(self, get_pdf, update_hold):
        """
        Test bug fix where mandate validation should not create a new
        dossier communication for the sponsor.
        """
        update_hold.return_value = True

        bank = self.env["res.bank"].create(
            {
                "name": "BCV",
                "bic": "BICBIC22123",
                "clearing": "234234",
                "acc_number": "01-044443-7",
            }
        )

        bank_account = self.env["res.partner.bank"].create(
            {
                "partner_id": self.michel.commercial_partner_id.id,
                "bank_id": bank.id,
                "acc_number": "01-044443-7",
                "l10n_ch_isr_subscription_chf": "010444437",
            }
        )
        self.mandates = self.env["account.banking.mandate"].search(
            [("partner_id", "=", self.michel.commercial_partner_id.id)]
        )
        self.mandates.write({"state": "draft"})
        bank_account.mandate_ids = self.mandates
        self.michel.commercial_partner_id.bank_ids = bank_account

        f_path = "addons/partner_communication_switzerland/static/src/test.pdf"
        with file_open(f_path, "rb") as pdf_file:
            get_pdf.return_value = (pdf_file.read(), "pdf")

        # Creation of the sponsorship contract
        child = self.create_child(self.ref(11))
        sponsorship = self.create_contract(
            {
                "partner_id": self.michel.id,
                "group_id": self.sp_group.id,
                "child_id": child.id,
            },
            [{"amount": 50.0}],
        )
        # Check the sponsorship is in waiting mandate state
        self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.state, "mandate")

        # Check the communication is generated after sponsorship validation
        new_dossier = self.env.ref("partner_communication_switzerland.planned_dossier")
        partner_communications = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", self.michel.id),
                ("state", "=", "pending"),
                ("config_id", "=", new_dossier.id),
            ]
        )
        self.assertTrue(partner_communications)

        # Remove the new dossier communication
        partner_communications.unlink()

        # Validate a mandate to make the sponsorship in waiting state.
        self.mandates.validate()
        self.assertEqual(sponsorship.state, "waiting")

        # Check that no new communication is generated
        partner_communications = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", self.michel.id),
                ("state", "=", "pending"),
                ("config_id", "=", new_dossier.id),
            ]
        )
        self.assertFalse(partner_communications)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_bvr_generation(self, get_pdf, update_hold):
        communications = self._create_communication(get_pdf, update_hold)
        get_pdf.return_value = (b"pdf", "pdf")
        bvr = communications.get_birthday_bvr()
        self.assertTrue("Birthday Gift.pdf" in bvr)
        values = bvr["Birthday Gift.pdf"]
        self.assertEqual(values[0], "report_compassion.bvr_gift_sponsorship")
        self.assertEqual(b64decode(values[1]), get_pdf.return_value[0])

        graduation_bvr = communications.get_graduation_bvr()
        self.assertTrue("Graduation Gift.pdf" in graduation_bvr)
        values = graduation_bvr["Graduation Gift.pdf"]
        self.assertEqual(values[0], "report_compassion.bvr_gift_sponsorship")

        reminder_bvr = communications.get_reminder_bvr()
        self.assertEqual(reminder_bvr, dict())

    def _create_communication(self, get_pdf, update_hold):
        update_hold.return_value = True

        f_path = "addons/partner_communication_switzerland/static/src/test.pdf"
        with file_open(f_path, "rb") as pdf_file:
            get_pdf.return_value = pdf_file.read()

        child = self.create_child(self.ref(11))
        sponsorship = self.create_contract(
            {
                "partner_id": self.michel.id,
                "group_id": self.sp_group.id,
                "child_id": child.id,
            },
            [{"amount": 50.0}],
        )
        self.validate_sponsorship(sponsorship)

        new_dossier = self.env.ref("partner_communication_switzerland.planned_dossier")
        return self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", self.michel.id),
                ("state", "=", "pending"),
                ("config_id", "=", new_dossier.id),
            ]
        )

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_send(self, get_pdf, update_hold):
        self.env.user.firstname = "jason"
        get_pdf.return_value = (b"pdf", "pdf")
        communications = self._create_communication(get_pdf, update_hold)

        before = fields.Datetime.now()
        self.assertTrue(communications.send())

        job_created = self.env["partner.communication.job"].search(
            [("sent_date", ">=", before)], limit=1
        )
        self.assertTrue(job_created)
        self.assertEqual(job_created.state, "done")

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_private_convert_pdf(self, get_pdf, update_hold):
        update_hold.return_value = True

        f_path = "addons/partner_communication_switzerland/static/src/test.pdf"
        with file_open(f_path, "rb") as pdf_file:
            get_pdf.return_value = (pdf_file.read(), "pdf")

        child = self.create_child(self.ref(11))
        self.michel.letter_delivery_preference = "physical"
        sponsorship = self.create_contract(
            {
                "partner_id": self.michel.id,
                "group_id": self.sp_group.id,
                "child_id": child.id,
            },
            [{"amount": 50.0}],
        )
        self.validate_sponsorship(sponsorship)
        default_template = self.env.ref("sbc_compassion.default_template")
        correspondence_data = {
            "template_id": default_template.id,
            "original_text": "my text",
            "sponsorship_id": sponsorship.id,
            "letter_image": base64.b64encode(get_pdf.return_value[0]),
        }
        letter = self.env["correspondence"].create(correspondence_data)

        config = self.env.ref("partner_communication_switzerland.child_letter_config")
        job = self.env["partner.communication.job"].create(
            {
                "partner_id": self.michel.id,
                "object_ids": letter.ids,
                "config_id": config.id,
            }
        )
        self.assertEqual(len(job.attachment_ids), 1)
        self.assertRegex(job.attachment_ids[0].name, r"^Supporter Letter")

    def test_resetting_password(self):
        partner_communications = self.env["partner.communication.job"]
        demo_user = self.env.ref("base.user_demo")
        jobs_before = partner_communications.search([])

        demo_user.action_reset_password()

        new_job = partner_communications.search([]) - jobs_before
        self.assertEqual(len(new_job), 1)
        self.assertTrue(new_job.send())
        self.assertIn("A password reset was requested", new_job.body_html)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_co_3598(self, get_pdf, update_hold):
        update_hold.return_value = True
        f_path = "addons/partner_communication_switzerland/static/src/test.pdf"
        with file_open(f_path, "rb") as pdf_file:
            get_pdf.return_value = (pdf_file.read(), "pdf")

        child = self.create_child(self.ref(11))
        partner = self.michel
        correspondent = self.david

        correspondent.letter_delivery_preference = "both"
        sponsorship = self.create_contract(
            {
                "partner_id": partner.id,
                "group_id": self.sp_group.id,
                "child_id": child.id,
                "correspondent_id": correspondent.id,
            },
            [{"amount": 50.0}],
        )

        self.validate_sponsorship(sponsorship)

        default_template = self.env.ref("sbc_compassion.default_template")
        correspondence = self.env["correspondence"].create(
            {
                "sponsorship_id": sponsorship.id,
                "direction": "Beneficiary To Supporter",
                "template_id": default_template.id,
                "letter_image": base64.b64encode(get_pdf.return_value[0]),
            }
        )

        correspondence.send_communication()
        communication = correspondence.communication_id

        self.assertEqual(self.david, communication.partner_id)
        self.assertEqual(communication.send_mode, "both")

        self.assertTrue(communication.send())

        self.assertEqual(communication.state, "pending")
        self.assertEqual(communication.send_mode, "physical")

        self.assertTrue(communication.send())

        self.assertEqual(communication.state, "done")

    @mock.patch(mock_lifecycle)
    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_infos)
    @mock.patch(mock_invoicer)
    @mock.patch(mock_cleaner)
    @mock.patch(mock_release_hold)
    def test_draft_sub_cancel_communication(
        self, release_mock, cleaner, invoicer, get_infos, hold_mock, lifecyle_mock
    ):
        hold_mock.return_value = True
        get_infos.return_value = True
        invoicer.return_value = True
        cleaner.return_value = True
        release_mock.return_value = True
        lifecyle_mock.return_value = True

        child = self.create_child(self.ref(11))
        partner = self.michel

        sponsorship = self.create_contract(
            {
                "partner_id": partner.id,
                "group_id": self.sp_group.id,
                "child_id": child.id,
            },
            [{"amount": 50.0}],
        )

        sponsorship.force_activation()

        self.assertTrue(sponsorship.is_active)

        child.child_departed()
        self.assertEqual(sponsorship.sds_state, "sub_waiting")

        sub_child = self.create_child(self.ref(11))

        self.env["sds.subsponsorship.wizard"].with_context(
            active_id=sponsorship.id
        ).create(
            {"state": "sub", "channel": "direct", "child_id": sub_child.id}
        ).create_subsponsorship()

        subsponsorship = sub_child.sponsorship_ids

        self.assertEqual(subsponsorship.state, "draft")

        no_sub = self.env.ref("partner_communication_switzerland.planned_no_sub")

        # Setup a sponsorship end wizard and put and end to the subsponsorship
        # that we just created.
        subreject = self.env.ref("sponsorship_compassion.end_reason_subreject")
        self.env["end.contract.wizard"].with_context(default_type="S").create(
            {
                "contract_ids": [(6, 0, subsponsorship.ids)],
                "end_reason_id": subreject.id,
            }
        ).end_contract()

        self.assertEqual(subsponsorship.state, "cancelled")

        no_sub_comm = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", partner.id),
                ("config_id", "=", no_sub.id),
                ("object_ids", "in", subsponsorship.ids),
            ]
        )

        self.assertNotEqual(no_sub_comm, False)

    @mock.patch(mock_new_dossier)
    @mock.patch(mock_update_hold)
    def test_new_dossier_called_once(self, hold_mock, new_dossier_mock):
        hold_mock.return_value = True
        number_call = 0

        def increase_number_call():
            nonlocal number_call
            number_call += 1
            return True

        new_dossier_mock.return_value = increase_number_call()

        child = self.create_child(self.ref(11))
        partner = self.michel

        correspondent = self.david

        sc_contract = self.create_contract(
            {
                "partner_id": partner.id,
                "correspondent_id": correspondent.id,
                "group_id": self.create_group({"partner_id": partner.id}).id,
                "child_id": child.id,
                "type": "SC",
            },
            [],
        )

        sc_contract.contract_waiting()

        self.assertEqual(number_call, 1)

    @mock.patch(mock_update_hold)
    def test_no_unwanted_comm_co_3696(self, hold_mock):
        hold_mock.return_value = True

        child = self.create_child(self.ref(11))
        partner = self.michel
        correspondent = self.david

        self.assertIsNot(partner.email, False)

        sc_contract = self.create_contract(
            {
                "partner_id": partner.id,
                "correspondent_id": correspondent.id,
                "group_id": self.create_group({"partner_id": partner.id}).id,
                "child_id": child.id,
                "type": "SC",
            },
            [],
        )

        sc_contract.contract_waiting()

        # SC contract are immediately activate
        self.assertEqual(sc_contract.state, "active")

        all_contract_comm = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", correspondent.id),
                ("model", "=", sc_contract._name),
                ("object_ids", "like", str(sc_contract.id)),
            ]
        )

        self.assertEqual(len(all_contract_comm), 2)

        self.assertIsNot(sc_contract, False)
