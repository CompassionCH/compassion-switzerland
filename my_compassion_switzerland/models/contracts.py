##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models

# The Swiss payment modes that collect through a bank instead of charging
# online, mapped onto what the sponsor still has to do for the first amount
# to arrive. Matched by xmlid, because the one mode that cannot be told apart
# by its payment method is Permanent Order: a plain "manual" mode, like a
# dozen unrelated back-office ones.
CH_PENDING_PAYMENT_MODES = {
    "my_compassion_switzerland.payment_mode_ebill": "ebill",
    "sponsorship_switzerland.payment_mode_permanent_order": "permanent_order",
    "sponsorship_switzerland.payment_mode_lsv": "direct_debit",
    "sponsorship_switzerland.payment_mode_lsv_25th": "direct_debit",
    "sponsorship_switzerland.payment_mode_lsv_multi_months": "direct_debit",
    "sponsorship_switzerland.payment_mode_postfinance_dd": "direct_debit",
    "sponsorship_switzerland.payment_mode_postfinance_dd_25th": "direct_debit",
    "sponsorship_switzerland.payment_mode_postfinance_dd_multi_months": (
        "direct_debit"
    ),
}

# Fallback for a mode that only exists in the database, which is how the
# published Swiss set has always been decided. Read off the payment method,
# shared by every variant of one collection mechanism.
CH_PENDING_PAYMENT_METHODS = {
    "ebill": "ebill",
    "sepa.ch.dd": "direct_debit",
    "sepa_direct_debit": "direct_debit",
    "lsv": "direct_debit",
    "postfinance.dd": "direct_debit",
}


class RecurringContract(models.Model):
    _inherit = "recurring.contract"

    def _my2_ch_pending_payment_kind(self):
        """What a Swiss sponsor still has to do for the money to arrive.

        Every payment mode published in Switzerland today is bank-collected:
        eBill, Permanent Order and Postfinance Direct Debit take no online
        payment, so a signup reaches the thank-you page with nothing paid
        yet. The page has to say what happens next instead of implying a
        payment was taken - which is what this tells it (see
        templates/my2_new_sponsorship_thank_you.xml).

        False when there is nothing pending to announce:

        - a provider-backed mode charged the first month between the
          checkout and the thank-you page, so the sponsor has already paid;
        - a Write&Pray sponsorship deliberately carries no payment mode at
          all. It takes no money ever, so telling its sponsor that no
          payment has been taken *yet* would invent one they never agreed
          to.

        :return: "ebill", "permanent_order", "direct_debit", "other", or
            False.
        """
        self.ensure_one()
        mode = self.payment_mode_id
        if not mode or mode.payment_provider_id:
            return False
        for xml_id, kind in CH_PENDING_PAYMENT_MODES.items():
            if mode == self.env.ref(xml_id, raise_if_not_found=False):
                return kind
        return CH_PENDING_PAYMENT_METHODS.get(mode.payment_method_id.code, "other")

    def _my2_apply_details(self, values):
        """Also save the volunteering opt-in of the Swiss details form.

        Written after the shared implementation rather than merged into its
        own write, on purpose: it runs once the sponsor's real name is in
        place, so the "Potential volunteer" activity partner_compassion
        schedules from this write names a person instead of a placeholder.

        Only ever an opt-in. An unticked box leaves the flag alone, the same
        way the shared implementation leaves every empty field alone, so a
        sponsor who says nothing here never has a "no" written over a "yes"
        they gave somewhere else.
        """
        partner = super()._my2_apply_details(values)
        if values.get("volunteering") and not partner.interested_for_volunteering:
            partner.sudo().write({"interested_for_volunteering": True})
        return partner
