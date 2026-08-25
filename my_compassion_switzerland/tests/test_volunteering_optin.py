##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from .common import SwissCheckoutCase

CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')
ADVOCATE_PARAM = "partner_communication_switzerland.potential_advocate_fr"


@tagged("post_install", "-at_install")
class TestVolunteeringActivity(SwissCheckoutCase):
    """The "Potential volunteer" staff to-do partner_compassion schedules.

    It has always been written for a write() and has never run for a web
    signup, because everything about the partner used to arrive in one
    create(). The fast checkout creates the partner from an email address and
    writes the rest afterwards, so this is now a live notification and its
    conditions are worth pinning down.
    """

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            ADVOCATE_PARAM, str(self.env.user.id)
        )
        self.partner = self.env["res.partner"].create(
            {
                "firstname": "Jeanne",
                "lastname": "Volontaire",
                "lang": "fr_CH",
            }
        )

    def test_saying_yes_notifies_the_staff_once(self):
        self.partner.write({"interested_for_volunteering": True})
        activities = self._potential_volunteer_activities(self.partner)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.env.user)

    def test_saying_yes_twice_does_not_notify_twice(self):
        """More than one place writes this flag - the details form, the
        Wordpress connector, an import, a staff member re-saving the
        record."""
        self.partner.write({"interested_for_volunteering": True})
        self.partner.write({"interested_for_volunteering": True})
        self.assertEqual(len(self._potential_volunteer_activities(self.partner)), 1)

    def test_a_later_unrelated_write_does_not_notify_again(self):
        self.partner.write({"interested_for_volunteering": True})
        self.partner.write({"city": "Lausanne"})
        self.assertEqual(len(self._potential_volunteer_activities(self.partner)), 1)

    def test_not_saying_yes_notifies_nobody(self):
        self.partner.write({"interested_for_volunteering": False})
        self.assertFalse(self._potential_volunteer_activities(self.partner))

    def test_a_known_advocate_is_not_announced_as_a_potential_one(self):
        self.partner.advocate_details_id = self.env["advocate.details"].create(
            {"partner_id": self.partner.id}
        )
        self.partner.write({"interested_for_volunteering": True})
        self.assertFalse(self._potential_volunteer_activities(self.partner))

    def test_a_partner_without_a_language_does_not_break_the_write(self):
        """res.partner.lang is deliberately left empty on this model, and a
        partner created by a web flow has none - which used to make this
        path raise on lang[:2] the moment it became reachable."""
        nameless_lang = self.env["res.partner"].create(
            {"firstname": "Sans", "lastname": "Langue", "lang": False}
        )
        self.assertFalse(nameless_lang.lang)
        nameless_lang.write({"interested_for_volunteering": True})
        self.assertTrue(nameless_lang.interested_for_volunteering)

    def test_a_language_without_a_recipient_does_not_break_the_write(self):
        """A recipient can be configured for French, German and Italian and
        for nothing else, and asking the settings for one that does not
        exist raises instead of answering - so an English-speaking sponsor
        used to take the whole write down with them the moment this path
        became reachable."""
        english = self.env["res.partner"].create(
            {"firstname": "English", "lastname": "Speaker", "lang": "en_US"}
        )
        english.write({"interested_for_volunteering": True})
        self.assertTrue(english.interested_for_volunteering)
        # nobody to tell, so nobody is told - and the opt-in is still saved
        self.assertFalse(self._potential_volunteer_activities(english))


@tagged("post_install", "-at_install")
class TestVolunteeringOptIn(HttpCase, SwissCheckoutCase):
    """Where the opt-in is asked now that no wizard step asks it.

    It used to live on the wizard's communication-details step, which the
    fast checkout no longer runs in any flow. Its audience is unchanged -
    public signups - only the moment moved, from before the payment to the
    post-payment details form.
    """

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            ADVOCATE_PARAM, str(self.env.user.id)
        )
        self.signup = self._make_ch_signup(self.ebill_mode)

    def _open_form(self):
        token = self.signup._my2_issue_details_token()
        page = self.url_open(
            f"/my2/new-sponsorship/thank-you?sponsorship_id={self.signup.id}"
            f"&details_token={token}"
        )
        self.assertEqual(page.status_code, 200)
        csrf = CSRF_RE.search(page.text)
        self.assertTrue(csrf, "the details form should carry a csrf token")
        return page.text, csrf.group(1), token

    def _post_details(self, csrf, token, **fields_):
        values = {
            "csrf_token": csrf,
            "sponsorship_id": self.signup.id,
            "details_token": token,
            "firstname": "Jeanne",
            "lastname": "Dupont",
            # A landline on purpose: partner_compassion re-files a Swiss
            # mobile number onto res.partner.mobile (check_phone_and_mobile),
            # which would make an assertion on phone say nothing useful.
            "phone": "+41 21 123 45 67",
        }
        values.update(fields_)
        return self.url_open(
            "/my2/new-sponsorship/complete-details",
            data=values,
            allow_redirects=False,
        )

    def test_the_details_form_asks_the_opt_in(self):
        html, _csrf, _token = self._open_form()
        self.assertIn('name="volunteering"', html)
        self.assertIn('id="details_volunteering"', html)

    def test_the_form_asks_it_only_once(self):
        """A repeated field name would make Odoo read the wrong value: it
        keeps the first one it sees, so a companion hidden input would win
        over the ticked box."""
        html, _csrf, _token = self._open_form()
        self.assertEqual(html.count('name="volunteering"'), 1)

    def test_ticking_it_opts_the_sponsor_in_and_notifies_the_staff(self):
        _html, csrf, token = self._open_form()
        response = self._post_details(csrf, token, volunteering="1")
        self.assertEqual(response.status_code, 303)
        partner = self.signup.partner_id
        self.assertTrue(partner.interested_for_volunteering)
        self.assertEqual(len(self._potential_volunteer_activities(partner)), 1)

    def test_the_staff_is_told_the_sponsors_real_name(self):
        """The flag is written after the name, so the to-do names a person
        rather than the checkout placeholder."""
        _html, csrf, token = self._open_form()
        self._post_details(csrf, token, volunteering="1")
        partner = self.signup.partner_id
        self.assertFalse(partner.my2_name_placeholder)
        activity = self._potential_volunteer_activities(partner)
        self.assertEqual(len(activity), 1)
        self.assertIn("Dupont", partner.name)

    def test_leaving_it_alone_opts_nobody_in(self):
        _html, csrf, token = self._open_form()
        response = self._post_details(csrf, token)
        self.assertEqual(response.status_code, 303)
        partner = self.signup.partner_id
        self.assertFalse(partner.interested_for_volunteering)
        self.assertFalse(self._potential_volunteer_activities(partner))
        # the rest of the form still saved
        self.assertEqual(partner.phone, "+41 21 123 45 67")
        self.assertFalse(partner.my2_name_placeholder)

    def test_an_unticked_box_never_overwrites_an_earlier_yes(self):
        """The sponsor may have said yes somewhere else entirely; this form
        is an opt-in, not a preference page."""
        self.signup.partner_id.write({"interested_for_volunteering": True})
        _html, csrf, token = self._open_form()
        self._post_details(csrf, token)
        self.assertTrue(self.signup.partner_id.interested_for_volunteering)

    def test_the_tick_survives_a_bounced_submission(self):
        """A missing required field re-renders the form; nothing the sponsor
        already answered may be lost on the way."""
        _html, csrf, token = self._open_form()
        response = self._post_details(csrf, token, phone="", volunteering="1")
        self.assertEqual(response.status_code, 200)
        checkbox = re.search(r'<input[^>]*name="volunteering"[^>]*>', response.text)
        self.assertTrue(checkbox, "the form should come back with its checkbox")
        self.assertIn("checked", checkbox.group(0))
        self.assertFalse(self.signup.partner_id.interested_for_volunteering)


@tagged("post_install", "-at_install")
class TestVolunteeringWizardSeam(SwissCheckoutCase):
    """The wizard-side override, which the placeholder-name mechanism now
    runs through."""

    def setUp(self):
        super().setUp()
        self.child = self.env["compassion.child"].search([], limit=1)
        self.assertTrue(self.child, "the database needs a child")

    def _wizard(self, **values):
        return self.env["new.sponsorship.wizard"].create(
            {
                "sponsorship_type": "standard",
                "user_id": self.env.ref("base.public_user").id,
                "child_id": self.child.id,
                "company_id": self.ch_company.id,
                **values,
            }
        )

    def test_the_flag_is_added_on_top_of_the_placeholder_name(self):
        """Additive, and it has to stay additive: the shared implementation
        rewrites the name keys of a signup whose sponsor has not given a
        name yet, and must be left to do so."""
        wizard = self._wizard(email="ch-wizard@example.org", volunteering=True)
        self.assertTrue(wizard.details_deferred)
        vals = wizard._get_new_partner_vals()
        self.assertTrue(vals["interested_for_volunteering"])
        self.assertTrue(vals["my2_name_placeholder"])
        self.assertEqual(vals["lastname"], self.env["res.partner"].MY2_PLACEHOLDER_NAME)
        self.assertFalse(vals["firstname"])

    def test_a_real_name_is_left_alone(self):
        wizard = self._wizard(
            email="ch-wizard-named@example.org",
            firstname="Jeanne",
            lastname="Dupont",
        )
        vals = wizard._get_new_partner_vals()
        self.assertFalse(vals.get("my2_name_placeholder"))
        self.assertEqual(vals["lastname"], "Dupont")
        self.assertFalse(vals["interested_for_volunteering"])

    def test_the_flag_still_travels_with_a_posted_step(self):
        """No step asks it today, but this is the seam a step would use."""
        wizard = self._wizard()
        wizard.update({"volunteering": "1", "action": "next"})
        self.assertTrue(wizard.volunteering)
