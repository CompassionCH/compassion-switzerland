##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import Command

from odoo.addons.my_compassion.tests.common import DigitalSeamCase

EBILL_MODE = "my_compassion_switzerland.payment_mode_ebill"
PERMANENT_ORDER_MODE = "sponsorship_switzerland.payment_mode_permanent_order"
POSTFINANCE_DD_MODE = "sponsorship_switzerland.payment_mode_postfinance_dd"


class SwissCheckoutCase(DigitalSeamCase):
    """Fixtures of a Swiss fast-checkout signup.

    Every payment mode Switzerland publishes is bank-collected, so a
    bank-collected signup - not the provider-backed one the shared base case
    builds - is what a Swiss checkout actually produces.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ch_company = cls.env.ref("base.main_company")
        cls.ebill_mode = cls.env.ref(EBILL_MODE)
        cls.permanent_order_mode = cls.env.ref(PERMANENT_ORDER_MODE)
        cls.postfinance_dd_mode = cls.env.ref(POSTFINANCE_DD_MODE)
        cls.ch_modes = (
            cls.ebill_mode | cls.permanent_order_mode | cls.postfinance_dd_mode
        )
        # Which modes are published is live configuration, decided in the
        # database rather than shipped as module data, so it is set here
        # instead of being read - a test that depended on it would pass or
        # fail on whichever database it runs against.
        cls.ch_modes.write({"is_published": True})

    def _make_ch_signup(self, mode, email="ch-checkout@example.org", **partner_vals):
        """A Swiss signup on `mode`, still waiting for its sponsor's name.

        The state the fast checkout leaves behind: a partner created from an
        email address alone, carrying the placeholder name until the
        post-payment details form replaces it.
        """
        partner = self.env["res.partner"].create(
            {
                "firstname": "Swiss",
                "lastname": "Checkout",
                "email": email,
                # Swiss staff are notified per language, so a partner without
                # one is the interesting case and has to be chosen, never
                # inherited by accident.
                "lang": "fr_CH",
                "country_id": self.env.ref("base.ch").id,
                **partner_vals,
            }
        )
        partner.write(
            {
                "lastname": self.env["res.partner"].MY2_PLACEHOLDER_NAME,
                "firstname": False,
                "my2_name_placeholder": True,
                "phone": False,
            }
        )
        group = self.env["recurring.contract.group"]._find_or_create_group(
            partner, self.ch_company, mode
        )
        product = self.env["product.product"].search(
            [
                ("default_code", "=", "sponsorship"),
                ("company_id", "in", [self.ch_company.id, False]),
            ],
            limit=1,
        )
        self.assertTrue(product, "the database needs the sponsorship product")
        contract = (
            self.env["recurring.contract"]
            .with_context(no_upsert=True)
            .create(
                {
                    "partner_id": partner.id,
                    "group_id": group.id,
                    "type": "O",
                    "contract_line_ids": [
                        Command.create(
                            {"product_id": product.id, "amount": 42, "quantity": 1}
                        )
                    ],
                }
            )
        )
        contract.my2_signup = True
        return contract

    def _potential_volunteer_activities(self, partner):
        """The staff to-dos partner_compassion schedules for an opt-in."""
        return self.env["mail.activity"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("summary", "=", "Potential volunteer"),
            ]
        )
