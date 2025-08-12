odoo.define("my_compassion", function (require) {
    "use strict";

    const ToastService = require("my_compassion.toast_service");
    const rpc = require("web.rpc");

    const form = document.querySelector("form");
    if (!form) return;

    form.addEventListener("submit", onSubmit);

    async function onSubmit(event) {
        // Prevent default form submission to handle the process manually
        event.preventDefault();

        let data;
        try {
            data = await collectFormData();
        } catch (error) {
            return ToastService.error(error.message);
        }

        try {
            const result = await registerVolunteer(data);
        } catch (error) {
            ToastService.error(
                "An error occurred while processing your request. Please try again or contact support."
            );
        }
    }

    async function collectFormData() {
        // Collect data from the form fields
        const title = document.getElementById("mrs")?.checked ? "Mrs." : "Mr.";
        const firstname = document.getElementById("volunteer_form_firstname")?.value.trim();
        const lastname = document.getElementById("volunteer_form_lastname")?.value.trim();
        const email = document.getElementById("volunteer_form_email")?.value.trim();
        const phone_number = document.getElementById("volunteer_form_phone_number")?.value.trim();
        const church = document.getElementById("volunteer_form_church")?.value.trim();

        // Collect all checked volunteer roles
        const volunteer_roles = Array.from(
            document.querySelectorAll('input[name="volunteer_roles"]:checked')
        ).map(cb => cb.value);

        // Collect comments
        const comments = document.querySelector('textarea[name="comments"]')?.value.trim();

        const lang = odoo.session_info?.user_context?.lang || "en_US";

        // Validate inputs
        if (!title) throw new Error("Please select a title");
        if (!firstname) throw new Error("Please enter your first name");
        if (!lastname) throw new Error("Please enter your last name");
        if (!email) throw new Error("Please enter your email address");
        if (!phone_number) throw new Error("Please enter your phone number");

        return {
            title,
            firstname,
            lastname,
            email,
            phone_number,
            church,
            volunteer_roles,
            comments,
            lang,
        };
    }

    /**
     * Sends the volunteering form data the backend via RPC.
     *
     * The backend is expected to indicate that the request was successful and a mail was send to the user and
     * to compassion
     *
     * @function
     * @param {Object} data - The data payload to send with the request.
     *
     * @returns {Promise<Object>} A promise that resolves with the backend response.
     */
    function registerVolunteer(data) {
        return rpc.query({
            route: "/my2/volunteering/register",
            params: data,
        });
    }
});