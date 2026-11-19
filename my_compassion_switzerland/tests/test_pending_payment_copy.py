##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import tagged
from odoo.tests.common import HttpCase

from .common import SwissCheckoutCase

NOTICE = 'id="ch_pending_payment_notice"'


@tagged("post_install", "-at_install")
class TestPendingPaymentKind(SwissCheckoutCase):
    """Which Swiss signups still owe a payment, and which do not.

    The thank-you page is written for a sponsor who has just paid. No mode
    published in Switzerland takes an online payment, so this is what tells
    the page to say what is still to come instead.
    """

    def test_ebill_is_pending_until_the_sponsor_approves_the_invoice(self):
        signup = self._make_ch_signup(self.ebill_mode)
        self.assertEqual(signup._my2_ch_pending_payment_kind(), "ebill")

    def test_permanent_order_is_pending_until_the_sponsor_sets_it_up(self):
        signup = self._make_ch_signup(self.permanent_order_mode)
        self.assertEqual(signup._my2_ch_pending_payment_kind(), "permanent_order")

    def test_postfinance_direct_debit_is_pending_until_the_mandate_exists(self):
        signup = self._make_ch_signup(self.postfinance_dd_mode)
        self.assertEqual(signup._my2_ch_pending_payment_kind(), "direct_debit")

    def test_lsv_is_recognised_as_a_direct_debit_too(self):
        """LSV is published alongside the three modes the decision named.

        It is the same mechanism as the Postfinance debit and needs the same
        answer, which is why the classification is not a list of three.
        """
        lsv = self.env.ref("sponsorship_switzerland.payment_mode_lsv")
        signup = self._make_ch_signup(lsv)
        self.assertEqual(signup._my2_ch_pending_payment_kind(), "direct_debit")

    def test_an_unknown_bank_mode_still_gets_an_answer(self):
        """A mode created in the database, which is how they are created."""
        mode = self.env["account.payment.mode"].create(
            {
                "name": "Cash At The Office",
                "company_id": self.ch_company.id,
                "bank_account_link": "variable",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "payment_order_ok": False,
            }
        )
        signup = self._make_ch_signup(mode)
        self.assertEqual(signup._my2_ch_pending_payment_kind(), "other")

    def test_an_online_mode_has_nothing_pending(self):
        """The sponsor paid on the way here: nothing to announce."""
        contract = self._make_digital_contract()
        self.assertTrue(contract.payment_mode_id.payment_provider_id)
        self.assertFalse(contract._my2_ch_pending_payment_kind())

    def test_a_sponsorship_without_a_payment_mode_has_nothing_pending(self):
        """Write&Pray, which never involves a payment at all.

        Saying "no payment has been made yet" there would announce a payment
        that is never coming.
        """
        signup = self._make_ch_signup(self.env["account.payment.mode"])
        self.assertFalse(signup.payment_mode_id)
        self.assertFalse(signup._my2_ch_pending_payment_kind())


@tagged("post_install", "-at_install")
class TestPendingPaymentCopy(HttpCase, SwissCheckoutCase):
    """The copy itself, on the page the sponsor actually lands on."""

    def _thank_you(self, signup):
        page = self.url_open(
            f"/my2/new-sponsorship/thank-you?sponsorship_id={signup.id}"
        )
        self.assertEqual(page.status_code, 200)
        return page.text

    def test_ebill_page_says_nothing_is_debited_yet(self):
        html = self._thank_you(self._make_ch_signup(self.ebill_mode))
        self.assertIn(NOTICE, html)
        self.assertIn("No payment has been made yet.", html)
        self.assertIn("Your E-Bill connection with Compassion is set up.", html)

    def test_permanent_order_page_promises_the_payment_details(self):
        html = self._thank_you(self._make_ch_signup(self.permanent_order_mode))
        self.assertIn(NOTICE, html)
        self.assertIn("standing order with your bank.", html)

    def test_direct_debit_page_promises_the_authorisation(self):
        html = self._thank_you(self._make_ch_signup(self.postfinance_dd_mode))
        self.assertIn(NOTICE, html)
        self.assertIn("direct debit authorisation", html)

    def test_the_kinds_do_not_leak_into_each_other(self):
        html = self._thank_you(self._make_ch_signup(self.permanent_order_mode))
        self.assertNotIn("Your E-Bill connection with Compassion is set up.", html)
        self.assertNotIn("direct debit authorisation", html)

    def test_an_online_payment_page_keeps_the_plain_thank_you(self):
        html = self._thank_you(self._make_digital_contract())
        self.assertNotIn(NOTICE, html)
        self.assertNotIn("No payment has been made yet.", html)

    def test_a_sponsorship_without_a_mode_keeps_the_plain_thank_you(self):
        signup = self._make_ch_signup(self.env["account.payment.mode"])
        html = self._thank_you(signup)
        self.assertNotIn(NOTICE, html)

    def test_the_notice_comes_before_the_details_form(self):
        """What happened to their money, before one more question."""
        signup = self._make_ch_signup(self.ebill_mode)
        token = signup._my2_issue_details_token()
        page = self.url_open(
            f"/my2/new-sponsorship/thank-you?sponsorship_id={signup.id}"
            f"&details_token={token}"
        )
        self.assertEqual(page.status_code, 200)
        html = page.text
        self.assertIn("/my2/new-sponsorship/complete-details", html)
        self.assertLess(
            html.index(NOTICE),
            html.index("/my2/new-sponsorship/complete-details"),
        )

    def test_a_settled_signup_is_not_told_a_payment_is_pending(self):
        """The notice is about the payment, not about the missing name.

        A Swiss signup whose sponsor has already given their name still owes
        the same bank payment, so it still says so - keying it on the details
        form instead would have made the message disappear halfway through.
        """
        signup = self._make_ch_signup(self.ebill_mode)
        signup.partner_id._my2_replace_placeholder_name("Jeanne", "Dupont")
        self.assertFalse(signup._my2_details_pending())
        html = self._thank_you(signup)
        self.assertIn(NOTICE, html)


@tagged("post_install", "-at_install")
class TestPendingPaymentRouting(SwissCheckoutCase):
    """No provider page is shown for a Swiss mode, which is what makes the
    adjusted copy the only change needed."""

    def test_no_swiss_published_mode_has_an_online_provider(self):
        published = (
            self.env["account.payment.mode"]
            .sudo()
            .search(
                [
                    ("is_published", "=", True),
                    ("company_id", "=", self.ch_company.id),
                ]
            )
        )
        self.assertTrue(published, "Switzerland should publish some mode")
        self.assertFalse(
            published.filtered("payment_provider_id"),
            "a provider-backed Swiss mode would need the payment page back",
        )
        # and every one of them gets an answer from the classification, so
        # none of them can reach the page with nothing said
        for mode in published:
            signup = self._make_ch_signup(mode, email=f"ch-mode-{mode.id}@example.org")
            self.assertTrue(
                signup._my2_ch_pending_payment_kind(),
                f"{mode.name} says nothing about its pending payment",
            )

    def test_a_line_still_gets_created(self):
        """Guards the fixture itself: an empty contract would make every
        assertion above pass for the wrong reason."""
        signup = self._make_ch_signup(self.ebill_mode)
        self.assertTrue(signup.contract_line_ids)
        self.assertEqual(signup.contract_line_ids.mapped("amount"), [42])
        self.assertEqual(
            signup.contract_line_ids[0].product_id.default_code, "sponsorship"
        )
