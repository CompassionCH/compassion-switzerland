/*
 * Extends the existing NewSponsorshipWizard with eBill functionality.
 *
 * eBill is not a "pay now" method: it is a subscription the sponsor sets up
 * with their own bank. An email address is sent to PostFinance, which mails a
 * validation code back, and the code is what completes the setup. Only then
 * may the sponsorship be finished.
 *
 * Two checkout shapes, one sub-workflow:
 *  - The public fast checkout is a single page holding the email, the consent
 *    and one button per payment mode. Pressing the eBill button opens the
 *    setup inline with the email the sponsor already typed there (never asked
 *    twice), and the wizard is submitted for them once the code validates.
 *  - The logged-in flow still selects a mode in the #payment_method dropdown
 *    and finishes with #finish_button. There, the setup is opened by its own
 *    intro button and the finish button stays disabled until it succeeds.
 *
 * The script communicates with backend endpoints:
 *  - /ebill/current-user/contract  => checks if a contract exists (auth=user,
 *                                     so only asked in the logged-in flow)
 *  - /ebill/subscribe              => starts the eBill setup flow
 *  - /ebill/validate               => validation (and confirmation) step
 *
 * ------------------------------------------------------------------------------- */

import { NewSponsorshipWizard } from "@my_compassion/js/my2_new_sponsorship_wizard";
import { rpc } from "@web/core/network/rpc";

// Account.payment.method code of the eBill payment mode
// (my_compassion_switzerland.account_payment_method_ebill), carried by both
// the dropdown options and the fast checkout's mode buttons.
const EBILL_PAYMENT_CODE = "ebill";

NewSponsorshipWizard.include({
  events: {
    ...NewSponsorshipWizard.prototype.events,
    "change #payment_method": "_onPaymentMethodChange",
    "click #start_ebill_workflow_btn": "_onStartEbillWorkflow",
    "click #ebill_content_container button[type='submit']":
      "_onEbillFormSubmit",
    "click #ebill_content_container a[type='submit']": "_onEbillFormSubmit",
  },

  /**
   * @override
   *
   * State is set up here rather than in start(), and per instance rather
   * than as a property of the include: an object literal on the include
   * would be one object shared by every instance of the widget, and the
   * events above are already delegated before start() runs - a click
   * landing in that window would read has_contract off undefined.
   */
  init: function () {
    this._super.apply(this, arguments);
    this._eBill = { has_contract: false, partner: null, contract: null };
    // The mode button that opened the setup, re-pressed once the code
    // validates so the wizard finishes through its normal path.
    this._eBillPendingButton = null;
    this._eBillDone = false;
  },

  /**
   * @override
   */
  start: async function () {
    this._super.apply(this, arguments);
    this._initEbillState();
  },

  /**
   * Checks if user has already an ebill contract.
   *
   * Only in the logged-in flow: the route authenticates, and a public
   * visitor of the fast checkout has no contract to find anyway.
   * @private
   */
  _initEbillState: function () {
    if (!this.$("#payment_method").length) {
      return Promise.resolve();
    }
    return rpc("/ebill/current-user/contract", {})
      .then((eBillInfoOfCurrentUser) => {
        this._eBill = eBillInfoOfCurrentUser;
        this._onPaymentMethodChange();
      })
      .catch((err) => {
        console.warn("Could not check existing eBill contract:", err);
      });
  },

  /**
   * POSTs form-encoded params to an eBill route and returns the HTML fragment.
   * @private
   * @param {String} action - The route to POST to
   * @param {Object} params - The form parameters
   * @returns {Promise<String>} - The HTML fragment
   */
  _postEbillForm: async function (action, params) {
    const response = await fetch(action, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ ...params, csrf_token: odoo.csrf_token }),
    });
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.text();
  },

  /**
   * The email address the sponsor gave the checkout itself.
   *
   * Deliberately blind to the eBill fragment's own email fields: they carry
   * the same id/name and would shadow the wizard's one once the fragment is
   * in the DOM.
   * @private
   * @returns {String}
   */
  _getCheckoutEmail: function () {
    const container = this.el.querySelector("#ebill_content_container");
    const inputs = Array.from(
      this.el.querySelectorAll("input[name='email']"),
    ).filter((input) => !container || !container.contains(input));
    return (inputs.length ? inputs[0].value : "").trim();
  },

  /**
   * Looks an eBill fragment field up inside the fragment only, for the same
   * reason as _getCheckoutEmail.
   * @private
   * @param {String} selector
   * @returns {String}
   */
  _getEbillFragmentValue: function (selector) {
    return (
      this.$("#ebill_content_container").find(selector).val() || ""
    ).trim();
  },

  /**
   * Puts an eBill fragment in the container: themed, and kept out of the
   * wizard's own form data.
   *
   * The container sits inside the wizard's <form>, and the fragment brings
   * a <form> of its own. Assigning it as innerHTML there makes the HTML
   * parser drop that nested start tag, which leaves the fragment's fields
   * owned by the wizard form and serialized with it on the next step call.
   * One of them is an "email", the same name the checkout's own field has
   * and later in the document, so it would win - and the retry fragment's
   * empty one would blank the address the sponsor typed. Dropping the names
   * costs nothing: every field in here is read by id, and the fragment's
   * own form action is never used because every submit in it is
   * intercepted (_onEbillFormSubmit).
   * @private
   * @param {String} html - The fragment as the eBill route returned it.
   */
  _setEbillFragment: function (html) {
    const $container = this.$("#ebill_content_container");
    $container.html(this._applyMy2StylesToEbill(html));
    $container.find("[name]").removeAttr("name");
  },

  /**
   * @override
   *
   * The fast checkout's payment-mode buttons both pick a mode and submit the
   * page. eBill cannot be submitted that way: its setup has to succeed first,
   * or the sponsorship would be created with an eBill mode no bank knows
   * about. So the first press opens the setup instead of stepping, and the
   * step happens by itself once the code validates.
   */
  _onStepClick: function (ev) {
    const isEbillButton =
      $(ev.currentTarget).data("payment-code") === EBILL_PAYMENT_CODE;
    if (isEbillButton && !this._eBillDone && !this._eBill.has_contract) {
      ev.preventDefault();
      this._startEbillSetup($(ev.currentTarget));
      return undefined;
    }
    return this._super.apply(this, arguments);
  },

  /**
   * Opens the eBill setup for the fast checkout, straight on the validation
   * code: the email of the page is what the code is sent to, so there is
   * nothing left to ask before it.
   *
   * The page is validated first, exactly as pressing any other mode button
   * would - an eBill setup started from an empty or malformed email address
   * would only send the code into the void.
   * @private
   * @param {jQuery} $button - The mode button that was pressed.
   */
  _startEbillSetup: function ($button) {
    if (!this._validateForm()) {
      return;
    }
    const email = this._getCheckoutEmail();
    if (!email) {
      return;
    }
    this._eBillPendingButton = $button;
    this.$("#ebill_setup_container").removeClass("d-none");
    this.$("#ebill_error").addClass("d-none");
    this.$("#ebill_loading").removeClass("d-none");
    const container = this.el.querySelector("#ebill_setup_container");
    if (container) {
      container.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    this._postEbillForm("/ebill/subscribe", { is_integrated: true, email })
      .then((html) => {
        this._setEbillFragment(html);
      })
      .catch((err) => {
        console.error(err);
        this.$("#ebill_loading").addClass("d-none");
        this.$("#ebill_error").removeClass("d-none");
      });
  },

  /**
   * Handles the change event on the payment method dropdown.
   * @private
   */
  _onPaymentMethodChange: function () {
    const $selectedOption = this.$("#payment_method option:selected");
    const isEBill = $selectedOption.data("payment-code") === EBILL_PAYMENT_CODE;

    if (isEBill && !this._eBill.has_contract) {
      this.$("#ebill_setup_container").toggleClass("d-none", false);
      this.$("#finish_button").prop("disabled", true);
    } else {
      this.$("#ebill_setup_container").toggleClass("d-none", true);
      this.$("#finish_button").prop("disabled", false);
    }
  },

  /**
   * Starts the E-Bill workflow when the "Set up" button is clicked.
   *
   * The intro button only exists in the dropdown flow, whose page holds no
   * email address: the one of the logged-in sponsor is used instead, and the
   * fragment asks for one when there is none.
   * @private
   * @param {Event} ev
   */
  _onStartEbillWorkflow: function (ev) {
    ev.preventDefault();

    const params = {
      is_integrated: true,
      email: this._eBill.partner?.email || this._getCheckoutEmail(),
    };

    this._postEbillForm("/ebill/subscribe", params)
      .then((html) => {
        this.$("#ebill_setup_container").show();
        this._setEbillFragment(html);
        this.$("#finish_button").prop("disabled", true);
      })
      .catch(console.error);
  },

  /**
   * Intercepts form submissions inside the E-Bill container and handles them
   * via a fragment-returning POST.
   * @private
   * @param {Event} ev
   */
  _onEbillFormSubmit: function (ev) {
    const form = $(ev.currentTarget).closest("form");
    const noValidationNeeded = $(ev.currentTarget).is("[formnovalidate]");

    if (form.length && !form[0].checkValidity() && !noValidationNeeded) {
      form[0].reportValidity();
      return;
    }

    ev.preventDefault();
    ev.stopPropagation();

    const action = ev.currentTarget.dataset.action;

    const params = {
      is_integrated: true,
    };

    if (!action) {
      console.error("The clicked button is missing a 'data-action' attribute.");
      return;
    } else if (action === "/ebill/subscribe") {
      params.email =
        this._getEbillFragmentValue("#email_input") ||
        this._getEbillFragmentValue("#email") ||
        this._getCheckoutEmail();
    } else if (action === "/ebill/validate") {
      params.validation_code = this._getEbillFragmentValue(
        "#validation_code_input",
      );
      params.token = this._getEbillFragmentValue("#token");
      params.email =
        this._getEbillFragmentValue("#email") || this._getCheckoutEmail();
    }

    this._postEbillForm(action, params)
      .then((html) => {
        this._setEbillFragment(html);
        const doneSuccessfully =
          this.$("#ebill_content_container #ebill-success-marker").length > 0;
        if (doneSuccessfully) {
          this._eBillDone = true;
          this.$("#finish_button").prop("disabled", false);
          this._continueAfterEbill();
        }
      })
      .catch(console.error);
  },

  /**
   * Finishes the fast checkout once the eBill setup succeeded.
   *
   * Presses the mode button the sponsor pressed to get here, so the step goes
   * through the wizard's own path (the eBill mode travels with it) instead of
   * a second, parallel way of submitting the page. No-op in the dropdown
   * flow, which has its own finish button and a sponsor to press it.
   * @private
   */
  _continueAfterEbill: function () {
    const $button = this._eBillPendingButton;
    if (!$button || !$button.length) {
      return;
    }
    this._eBillPendingButton = null;
    $button.trigger("click");
  },

  /**
   * Applies Compassion theme styles to the eBill HTML.
   * @private
   * @param {String} html The original HTML.
   * @returns {String} The styled HTML.
   */
  _applyMy2StylesToEbill: function (html) {
    if (!html) {
      return "";
    }
    return html
      .replace(
        "btn btn-primary",
        "btn btn--compact-filled btn--radius-pill bg-core-blue text-pure-white",
      )
      .replace(
        "btn btn-secondary",
        "btn btn--compact-filled btn--radius-pill bg-low-yellow text-black",
      )
      .replace("alert alert-danger", "alert alert-danger text-black");
  },
});
