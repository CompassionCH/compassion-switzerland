/**
 * Volunteer Form Submission Handler
 * ---------------------------------
 * This script handles the submission of the volunteer registration form.
 * It collects user input, validates the data, and sends it to the backend via RPC.
 * Additionally, it provides smooth scrolling for internal anchor links on the page.
 *
 * Key Features:
 * - Collects data from text inputs, radio buttons, checkboxes, and textareas
 * - Validates required fields before sending
 * - Sends form data to `/my2/volunteering/register` via Odoo RPC
 * - Displays success or error messages using ToastService
 * - Smoothly scrolls to target sections when internal anchor links are clicked
 */
document.addEventListener("DOMContentLoaded", function () {
  odoo.define("my_compassion_switzerland.my2_volunteering", function (require) {
    "use strict";

    const ToastService = require("my_compassion.toast_service");
    const rpc = require("web.rpc");

    // Translation
    const core = require("web.core");
    const _t = core._t;

    /**
     * Collects and validates form data
     * @returns {Object} - The data object to send to the backend
     */
    async function collectFormData() {
      function getValueFromDocumentElementId(id) {
        const el = document.getElementById(id);
        return el ? el.value.trim() : "";
      }

      // Collect data from the form fields
      const titleSelect = document.getElementById("title_select");
      const title = titleSelect ? titleSelect.value : null;

      const firstname = getValueFromDocumentElementId(
        "volunteer_form_firstname"
      );
      const lastname = getValueFromDocumentElementId("volunteer_form_lastname");
      const email = getValueFromDocumentElementId("volunteer_form_email");
      const phone_number = getValueFromDocumentElementId(
        "volunteer_form_phone_number"
      );
      const church = getValueFromDocumentElementId("volunteer_form_church");

      // Collect all checked volunteer roles
      const volunteer_roles = Array.from(
        document.querySelectorAll('input[name="volunteer_roles"]:checked')
      ).map((cb) => cb.value);

      // Collect comments
      const commentsInput = document.querySelector('textarea[name="comments"]');
      const comments = commentsInput ? commentsInput.value : null;

      const lang =
        (odoo.session_info &&
          odoo.session_info.user_context &&
          odoo.session_info.user_context.lang) ||
        "en_US";

      // Validate inputs
      if (!title) throw new Error(_t("Please select a title"));
      if (!firstname) throw new Error(_t("Please enter your first name"));
      if (!lastname) throw new Error(_t("Please enter your last name"));
      if (!email) throw new Error(_t("Please enter your email address"));
      if (!phone_number) throw new Error(_t("Please enter your phone number"));
      if (volunteer_roles.length === 0)
        throw new Error(_t("Please select one or more volunteering options"));

      return {
        // Prepare the data object to send to the backend
        data: {
          title,
          firstname,
          lastname,
          email,
          phone_number,
          church,
          volunteer_roles,
          comments,
          lang,
        },
      };
    }

    /**
     * Sends the volunteering form data to the backend via RPC
     * @param {Object} data - The data payload
     * @returns {Promise<Object>} - Backend response
     */
    function registerVolunteer(data) {
      return rpc.query({
        route: "/my2/volunteering/register",
        params: data,
      });
    }

    /**
     * Handles form submission
     * - Prevents default submission
     * - Collects and validates form data
     * - Sends data to the backend via RPC
     * - Shows toast messages for success or failure
     * @param {Event} event - Submit event
     */
    async function onSubmit(event) {
      // Prevent default form submission to handle the process manually
      event.preventDefault();
      const form = event.target;

      let data = null;
      try {
        data = await collectFormData();
      } catch (error) {
        return ToastService.error(error.message);
      }

      try {
        const result = await registerVolunteer(data);
        if (result.success) {
          ToastService.success(
            _t(
              "Thank you for your interest in volunteering! A confirmation email has been sent to you."
            )
          );
          form.reset();
        } else {
          ToastService.error(
            result.error
              ? result.error
              : _t(
                  "There was an issue with your submission. Please check your inputs and try again."
                )
          );
        }
      } catch (error) {
        ToastService.error(
          error.message ||
            _t(
              "An error occurred while processing your request. Please try again or contact support."
            )
        );
      }
    }

    const form = document.querySelector("form");
    if (!form) return;

    form.addEventListener("submit", onSubmit);

    // Enable smooth scrolling for all internal anchor links
    document
      .querySelectorAll('a[href^="#volunteer_form_top"]')
      .forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
          e.preventDefault();
          const target = document.querySelector(this.getAttribute("href"));
          if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      });
  });
});
