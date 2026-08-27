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

from odoo.addons.my_compassion.controllers.my2_sponsorships import (
    OWN_SIGNUPS_SESSION_KEY,
)

from .common import SwissCheckoutCase

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
        """A recipient setting exists for French, German, Italian and
        English and for nothing else, and asking the settings for one that
        is not even a defined field raises instead of answering - so a
        sponsor in any other language used to take the whole write down
        with them the moment this path became reachable.

        Every language actually active on this database now has a
        recipient (see the English test below) - not because the guard
        stopped mattering, but because it now only matters for the next
        language to be installed. Spanish is activated here, inside the
        test's own rolled-back transaction, purely to have one of those to
        write onto a partner without also touching the live database.
        """
        self.env["res.lang"]._activate_lang("es_ES")
        no_recipient_partner = self.env["res.partner"].create(
            {"firstname": "Sin", "lastname": "Idioma", "lang": "es_ES"}
        )
        no_recipient_partner.write({"interested_for_volunteering": True})
        self.assertTrue(no_recipient_partner.interested_for_volunteering)
        # nobody to tell, so nobody is told - and the opt-in is still saved
        self.assertFalse(self._potential_volunteer_activities(no_recipient_partner))

    def test_an_english_speaker_notifies_the_configured_recipient(self):
        """English is the fallback for the fast checkout's placeholder
        partners, who have no language of their own until the details form
        is filled in - so it is the language most sponsors will actually
        resolve to, not an edge case."""
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.potential_advocate_en",
            str(self.env.user.id),
        )
        english = self.env["res.partner"].create(
            {"firstname": "English", "lastname": "Speaker", "lang": "en_US"}
        )
        english.write({"interested_for_volunteering": True})
        activities = self._potential_volunteer_activities(english)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.env.user)


@tagged("post_install", "-at_install")
class TestVolunteeringOptIn(HttpCase, SwissCheckoutCase):
    """Where the opt-in is asked now: the public "All set" summary page.

    It used to live on the wizard's communication-details step, then on the
    post-payment "Who shall we thank?" details form; both no longer ask it.
    Its audience is unchanged - public signups - only the moment moved
    again, from the details form to the summary shown once that form is
    done. That page has no form of its own, so the checkbox posts itself to
    /my2/new-sponsorship/volunteering on change instead of waiting to be
    collected by a submit button.
    """

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            ADVOCATE_PARAM, str(self.env.user.id)
        )
        self.signup = self._make_ch_signup(self.ebill_mode)
        # The details form is already done by the time the "All set" page
        # (and its checkbox) exists for a sponsor to see.
        self.signup.partner_id._my2_replace_placeholder_name("Jeanne", "Dupont")

    def _own_signup_session(self):
        """A session that proves this browser is the one that checked out.

        The real-world proof for a not-yet-authenticated visitor on this
        page - see MyCompassionNewSponsorshipController
        ._issue_details_token, which the volunteering route's own gate
        mirrors.
        """
        self.authenticate(
            None, None, session_extra={OWN_SIGNUPS_SESSION_KEY: [self.signup.id]}
        )

    def _post_optin(self, volunteering):
        return self.make_jsonrpc_request(
            "/my2/new-sponsorship/volunteering",
            {"sponsorship_id": self.signup.id, "volunteering": volunteering},
        )

    def test_the_all_set_page_shows_the_opt_in(self):
        self._own_signup_session()
        page = self.url_open(
            f"/my2/new-sponsorship/thank-you?sponsorship_id={self.signup.id}"
        )
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="all_set_volunteering"', page.text)

    def test_ticking_it_opts_the_sponsor_in_and_notifies_the_staff(self):
        self._own_signup_session()
        result = self._post_optin(True)
        self.assertTrue(result["success"])
        partner = self.signup.partner_id
        self.assertTrue(partner.interested_for_volunteering)
        self.assertEqual(len(self._potential_volunteer_activities(partner)), 1)

    def test_the_staff_is_told_the_sponsors_real_name(self):
        """setUp already replaced the placeholder before the checkbox could
        even be shown, so the to-do this schedules should always name a
        person, never the checkout placeholder."""
        self._own_signup_session()
        self._post_optin(True)
        partner = self.signup.partner_id
        self.assertFalse(partner.my2_name_placeholder)
        activity = self._potential_volunteer_activities(partner)
        self.assertEqual(len(activity), 1)
        self.assertIn("Dupont", partner.name)

    def test_unticking_it_opts_the_sponsor_back_out(self):
        """Unlike the old details-form field this replaced, this also
        accepts taking a tick back: the checkbox reflects live state on a
        page the sponsor can act from, not a one-shot form."""
        self.signup.partner_id.write({"interested_for_volunteering": True})
        self._own_signup_session()
        result = self._post_optin(False)
        self.assertTrue(result["success"])
        self.assertFalse(self.signup.partner_id.interested_for_volunteering)

    def test_a_stringified_false_does_not_opt_the_sponsor_in(self):
        """volunteering must be an actual JSON boolean: a naive
        bool(volunteering) would coerce the non-empty *string* "false" to
        True, silently opting a sponsor in while the caller's intent (and
        the {"success": True} it would still get back) looked like an
        opt-out. type="json" routes do not enforce a schema, so a caller
        sending the wrong JSON type is a real, reachable case, not just a
        hypothetical."""
        self._own_signup_session()
        result = self._post_optin("false")
        self.assertFalse(result["success"])
        self.assertFalse(self.signup.partner_id.interested_for_volunteering)

    def test_a_foreign_session_cannot_opt_someone_else_in(self):
        """No own-signup session and no authenticated match: a bare
        sponsorship_id in the request must not be enough to write anything -
        the same gate the details-form token enforces for that page."""
        result = self._post_optin(True)
        self.assertFalse(result["success"])
        self.assertFalse(self.signup.partner_id.interested_for_volunteering)

    def test_the_authenticated_sponsor_can_also_opt_in(self):
        """The other accepted proof, alongside the own-signup session: the
        sponsor came back already logged in rather than through the
        checkout session that created this signup."""
        user = self.env["res.users"].create(
            {
                "name": "Jeanne Dupont",
                "login": "jeanne-volunteer@example.org",
                "partner_id": self.signup.partner_id.id,
            }
        )
        self.authenticate(user.login, user.login)
        result = self._post_optin(True)
        self.assertTrue(result["success"])
        self.assertTrue(self.signup.partner_id.interested_for_volunteering)


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
