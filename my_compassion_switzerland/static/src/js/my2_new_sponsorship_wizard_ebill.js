/*
 * Extends the existing NewSponsorshipWizard with eBill functionality.
 * Detects when the user selects "eBill" as a payment method, shows the
 * eBill setup container, and disables the finish button until setup
 * is completed successfully.
 *
 * The script communicates with backend endpoints:
 *  - /ebill/current-user/contract  => checks if a contract exists
 *  - /ebill/subscribe              =>  starts the eBill setup flow
 *  - /ebill/validate, /ebill/confirm => validate and confirm steps
 *
 * ------------------------------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", function (event) {
  odoo.define(
    "my_compassion_switzerland.new_sponsorship_wizard_ebill",
    function (require) {
      "use strict";

      var publicWidget = require("web.public.widget");
      var rpc = require("web.rpc");
      var ajax = require("web.ajax");

      var NewSponsorshipWizard = publicWidget.registry.NewSponsorshipWizard;

      if (!NewSponsorshipWizard) {
        return;
      }

      NewSponsorshipWizard.include({
        events: _.extend({}, NewSponsorshipWizard.prototype.events, {
          "change #payment_method": "_onPaymentMethodChange",
          "click #start_ebill_workflow_btn": "_onStartEbillWorkflow",
          "click #ebill_content_container button[type='submit']":
            "_onEbillFormSubmit",
          "click #ebill_content_container a[type='submit']":
            "_onEbillFormSubmit",
        }),

        _eBill: { has_contract: false, partner: null, contract: null },

        /**
         * @override
         */
        start: async function () {
          this._super.apply(this, arguments);
          this._initEbillState();
        },

        /**
         * Checks if user has already an ebill contract.
         * @private
         */
        _initEbillState: function () {
          return rpc
            .query({
              route: "/ebill/current-user/contract",
              params: {},
            })
            .then((eBillInfoOfCurrentUser) => {
              this._eBill = eBillInfoOfCurrentUser;
              this._onPaymentMethodChange();
            })
            .catch((err) => {
              console.warn("Could not check existing eBill contract:", err);
            });
        },

        /**
         * Handles the change event on the payment method dropdown.
         * @private
         */
        _onPaymentMethodChange: function () {
          const selectedText = this.$("#payment_method option:selected").text();
          const isEBill = selectedText.includes("eBill");

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
         * @private
         * @param {Event} ev
         */
        _onStartEbillWorkflow: function (ev) {
          ev.preventDefault();

          const params = {
            is_integrated: true,
            email: this._eBill.partner?.email,
          };

          ajax
            .post("/ebill/subscribe", params)
            .then((html) => {
              this.$("#ebill_setup_container").show();
              html = this._applyMy2StylesToEbill(html);
              this.$("#ebill_content_container").html(html);
              this.$("#finish_button").prop("disabled", true);
            })
            .catch(console.error);
        },

        /**
         * Intercepts form submissions inside the E-Bill modal and handles them via rpc.
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
            console.error(
              "The clicked button is missing a 'data-action' attribute."
            );
            return;
          } else if (action === "/ebill/validate") {
            params.email =
              this.$("#email_input").val() ?? this.$("#email").val();
          } else if (action === "/ebill/confirm") {
            params.validation_code = this.$("#validation_code_input").val();
            params.token = this.$("#token").val();
            params.email = this.$("#email").val();
          }

          ajax
            .post(action, params)
            .then((html) => {
              html = this._applyMy2StylesToEbill(html);
              this.$("#ebill_content_container").html(html);
              const doneSuccessfully =
                this.$("#ebill_content_container #ebill-success-marker")
                  .length > 0;
              if (doneSuccessfully) {
                this.$("#finish_button").prop("disabled", false);
              }
            })
            .catch(console.error);
        },
        /**
         * Applies Compassion theme styles to the eBill HTML.
         * @private
         * @param {string} html The original HTML.
         * @returns {string} The styled HTML.
         */
        _applyMy2StylesToEbill: function (html) {
          if (!html) {
            return "";
          }
          return html
            .replace(
              "btn btn-primary",
              "btn btn--compact-filled btn--radius-pill bg-core-blue text-pure-white"
            )
            .replace(
              "btn btn-secondary",
              "btn btn--compact-filled btn--radius-pill bg-low-yellow text-black"
            )
            .replace("alert alert-danger", "alert alert-danger text-black");
        },
      });
    }
  );
});
