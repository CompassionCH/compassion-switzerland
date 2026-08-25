##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re
from pathlib import Path

from odoo.tests import tagged

from odoo.addons.my_compassion.controllers.my2_sponsorships import (
    MyCompassionNewSponsorshipController,
)
from odoo.addons.my_compassion.models.my2_new_sponsorship_wizard import (
    FAST_CHECKOUT_STEP,
)
from odoo.addons.website.tools import MockRequest

from .common import SwissCheckoutCase

PAYMENT_STEP = "my_compassion.new_sponsorship_wizard_step_payment_methods"

EBILL_JS = (
    Path(__file__).resolve().parents[1]
    / "static/src/js/my2_new_sponsorship_wizard_ebill.js"
)
EBILL_CODE_RE = re.compile(r'const EBILL_PAYMENT_CODE = "([^"]*)";')


@tagged("post_install", "-at_install")
class TestEbillCheckout(SwissCheckoutCase):
    """The DOM contract between the eBill sub-workflow and the checkout.

    The sub-workflow itself is JavaScript, and none of it is exercised here.
    What is: the hooks it reaches for have to actually be on the page it runs
    on, and the payment code it recognises has to be the one the page hands
    it. Both are server-rendered, and both broke silently the last time the
    checkout was rearranged.
    """

    def setUp(self):
        super().setUp()
        self.child = self.env["compassion.child"].search([], limit=1)
        self.assertTrue(self.child, "the database needs a child")
        self.website = self.env.ref("my_compassion.my2_website")

    def _wizard(self, public=True, **values):
        user = self.env.ref("base.public_user") if public else self.env.user
        return self.env["new.sponsorship.wizard"].create(
            {
                "sponsorship_type": "standard",
                "user_id": user.id,
                "child_id": self.child.id,
                "company_id": self.ch_company.id,
                **values,
            }
        )

    def _render(self, wizard):
        with MockRequest(self.env, website=self.website):
            return str(
                MyCompassionNewSponsorshipController._render_form_content(wizard)
            )

    # === The code the JS keys on ===

    def test_ebill_payment_code_is_the_one_the_js_looks_for(self):
        """The JS recognises the eBill button by a hardcoded payment code.

        It cannot import the data record, so this is the only place the two
        can be kept in step: renaming the payment method's code would
        otherwise turn the eBill button into a plain "finish the wizard"
        button, creating a sponsorship on a mode no bank was ever told
        about.
        """
        declared = EBILL_CODE_RE.search(EBILL_JS.read_text())
        self.assertTrue(declared, "the eBill script should declare a payment code")
        self.assertEqual(declared.group(1), self.ebill_mode.payment_method_id.code)

    # === The fast-checkout page ===

    def test_fast_checkout_page_carries_the_ebill_hooks(self):
        wizard = self._wizard()
        self.assertEqual(wizard.current_step, self.env.ref(FAST_CHECKOUT_STEP))
        html = self._render(wizard)
        self.assertIn('id="ebill_setup_container"', html)
        self.assertIn('id="ebill_content_container"', html)
        # what the JS toggles while it waits for the code, and what it shows
        # when the subscription could not be started at all
        self.assertIn('id="ebill_loading"', html)
        self.assertIn('id="ebill_error"', html)

    def test_ebill_setup_starts_hidden(self):
        """A sponsor who never picks eBill must not see its box."""
        html = self._render(self._wizard())
        container = re.search(r'<div id="ebill_setup_container"[^>]*>', html)
        self.assertTrue(container)
        self.assertIn("d-none", container.group(0))

    def test_ebill_gets_a_mode_button_carrying_its_code(self):
        wizard = self._wizard()
        self.assertIn(self.ebill_mode, wizard._get_payment_mode_buttons())
        html = self._render(wizard)
        self.assertIn(f'data-payment-mode="{self.ebill_mode.id}"', html)
        self.assertIn('data-payment-code="ebill"', html)

    def test_setup_box_sits_above_the_mode_buttons(self):
        """The box has to open where the sponsor is looking.

        It is appended to the step, and the buttons are rendered after the
        step by the form-content template - so the order is a property of
        that arrangement rather than of the eBill inheritance, and this is
        what notices if the two ever swap.
        """
        html = self._render(self._wizard())
        self.assertLess(
            html.index('id="ebill_setup_container"'),
            html.index("data-payment-mode"),
        )

    def test_fast_checkout_has_no_second_email_and_no_intro_button(self):
        """The page already asked for an email, so the setup starts on the
        code. The intro button belongs to the flow that has no email to
        start from."""
        html = self._render(self._wizard())
        self.assertNotIn('id="start_ebill_workflow_btn"', html)
        self.assertEqual(html.count('name="email"'), 1)

    # === The logged-in dropdown step, unchanged ===

    def test_dropdown_step_keeps_its_hooks_and_its_intro_button(self):
        wizard = self._wizard(public=False)
        self.assertEqual(wizard.current_step, self.env.ref(PAYMENT_STEP))
        html = self._render(wizard)
        self.assertIn('id="payment_method"', html)
        self.assertIn('id="ebill_setup_container"', html)
        self.assertIn('id="ebill_content_container"', html)
        self.assertIn('id="start_ebill_workflow_btn"', html)
        # the dropdown carries the code on its options, the way the change
        # handler reads it
        self.assertIn('data-payment-code="ebill"', html)
        # and it stays a dropdown: no mode button to intercept there
        self.assertNotIn("data-payment-mode", html)

    def test_an_unpublished_ebill_offers_no_button(self):
        """Un-publishing the mode is how Switzerland would withdraw eBill."""
        self.ebill_mode.is_published = False
        html = self._render(self._wizard())
        self.assertNotIn(f'data-payment-mode="{self.ebill_mode.id}"', html)
        # the container is part of the step, not of the button, so it stays -
        # harmless, because nothing can open it any more
        self.assertIn('id="ebill_setup_container"', html)
