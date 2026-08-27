/** @odoo-module **/

/*
 * Posts the "All set" summary page's volunteering checkbox on change.
 *
 * That page (my_compassion.my2_new_sponsorship_thank_you_page, the
 * request.env.user._is_public() branch) is a summary, not a wizard step: it
 * has no <form> and no submit button of its own, so the checkbox saves
 * itself instead of waiting to be collected by one. See
 * controllers/my2_sponsorships.py::sponsorship_volunteering_optin for the
 * write and its access gate.
 * ------------------------------------------------------------------------------- */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

export const NewSponsorshipVolunteeringOptin = publicWidget.Widget.extend({
  selector: "#all_set_volunteering",
  events: {
    change: "_onChange",
  },

  /**
   * @param {Event} ev
   */
  _onChange: function (ev) {
    const checkbox = ev.currentTarget;
    const checked = checkbox.checked;
    checkbox.disabled = true;
    rpc("/my2/new-sponsorship/volunteering", {
      sponsorship_id: checkbox.dataset.sponsorshipId,
      volunteering: checked,
    })
      .then(function (result) {
        if (!result || !result.success) {
          // Not authorized to touch this sponsorship (stale/foreign
          // session): the tick would not reflect anything actually saved.
          checkbox.checked = !checked;
        }
      })
      .catch(function () {
        checkbox.checked = !checked;
      })
      .finally(function () {
        checkbox.disabled = false;
      });
  },
});

publicWidget.registry.NewSponsorshipVolunteeringOptin =
  NewSponsorshipVolunteeringOptin;
