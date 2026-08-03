/** @odoo-module **/

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
 * - Displays success or error messages using the toast service
 * - Smoothly scrolls to target sections when internal anchor links are clicked
 *
 * The assets bundle loads this site-wide: everything is guarded on the
 * presence of the volunteering form (`form.volunteering-form`).
 */

import { whenReady } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { toast } from "@my_compassion/js/toast_service";

/**
 * Collects and validates form data
 * @returns {Object} - The data object to send to the backend
 */
function collectFormData() {
  const volunteerRoles = Array.from(
    document.querySelectorAll('input[name="volunteer_roles"]:checked'),
  ).map((cb) => cb.value);

  const commentsInput = document.querySelector('textarea[name="comments"]');
  const comments = commentsInput ? commentsInput.value : null;

  if (volunteerRoles.length === 0) {
    throw new Error(_t("Please select one or more volunteering options"));
  }

  return {
    data: {
      volunteer_roles: volunteerRoles,
      comments: comments,
    },
  };
}

/**
 * Toggles the loading state of the form
 * - Disables all form elements to prevent changes during submission
 * - Toggles the spinner visibility
 * @param {HTMLFormElement} form - The volunteering form
 * @param {Boolean} isLoading - Whether a submission is in flight
 */
function toggleFormLoading(form, isLoading) {
  const loader = document.getElementById("volunteering-loader");

  for (const element of form.elements) {
    element.disabled = isLoading;
  }

  loader?.classList.toggle("d-none", !isLoading);
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
  event.preventDefault();
  const form = event.target;

  let data = null;
  try {
    data = collectFormData();
  } catch (error) {
    toast.error(error.message);
    return;
  }

  toggleFormLoading(form, true);

  try {
    const result = await rpc("/my2/volunteering/register", data);
    if (result.success) {
      toast.success(
        _t(
          "Thank you for your interest in volunteering! A confirmation email has been sent to you.",
        ),
      );
      form.reset();
    } else {
      toast.error(
        result.error ||
          _t(
            "There was an issue with your submission. Please check your inputs and try again.",
          ),
      );
    }
  } catch (error) {
    toast.error(
      error.message ||
        _t(
          "An error occurred while processing your request. Please try again or contact support.",
        ),
    );
  } finally {
    toggleFormLoading(form, false);
  }
}

whenReady(() => {
  const volunteeringForm = document.querySelector("form.volunteering-form");
  if (!volunteeringForm) {
    return;
  }
  volunteeringForm.addEventListener("submit", onSubmit);

  // Enable smooth scrolling for all internal anchor links
  document
    .querySelectorAll('a[href^="#volunteer_form_top"]')
    .forEach((anchor) => {
      anchor.addEventListener("click", (event) => {
        event.preventDefault();
        const target = document.querySelector(anchor.getAttribute("href"));
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    });
});
