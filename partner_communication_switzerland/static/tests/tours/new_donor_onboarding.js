/**
 * End to end test of the new donor onboarding process. A brand new contact
 * makes a first donation and gets thanked for it, which starts the new
 * donors onboarding process.
 *
 * The data this tour relies on is set up in
 * partner_communication_switzerland/tests/test_new_donor_onboarding.py
 */
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const DONOR_LASTNAME = "Doe";
const DONATION_PRODUCT = "Donation";
const FIRST_BLOG_POST = "New Donors Onboarding - 1st Blog Post";
const SECOND_BLOG_POST = "New Donors Onboarding - 2nd Blog Post";

const goToDonor = () => [
  ...stepUtils.goToAppSteps("contacts.menu_contacts", "Back to Contacts"),
  {
    content: "Search the donor",
    trigger: ".o_searchview_input",
    run: `edit ${DONOR_LASTNAME}`,
  },
  {
    content: "Validate the search",
    trigger: ".o_searchview_input",
    run: "press Enter",
  },
  {
    content: "Open the donor",
    trigger: `.o_kanban_record:contains(${DONOR_LASTNAME})`,
    run: "click",
  },
];

/** Generates one onboarding communication for the donor from their form. */
const generateCommunication = (template) => [
  ...goToDonor(),
  {
    content: "Open the action menu of the donor",
    trigger: ".o_form_view .o_cp_action_menus i.fa-cog",
    run: "click",
  },
  {
    content: "Generate a communication for the donor",
    trigger: ".o-dropdown--menu span:contains(Generate Communications)",
    run: "click",
  },
  {
    content: `Look for the ${template} template`,
    trigger: ".modal div[name=model_id] input",
    run: `edit ${template}`,
  },
  {
    content: `Select the ${template} template`,
    trigger: `.ui-menu-item a:contains(${template})`,
    run: "click",
  },
  {
    content: "Generate the communication",
    trigger: ".modal button[name=generate]",
    run: "click",
  },
  {
    content: `The ${template} communication was generated`,
    trigger:
      `.o_data_row:contains(${DONOR_LASTNAME}) ` +
      `td[name=config_id]:contains(${template})`,
  },
];

registry.category("web_tour.tours").add("new_donor_onboarding", {
  url: "/odoo",
  steps: () => [
    ...stepUtils.goToAppSteps(
      "contacts.menu_contacts",
      "Open the Contacts app",
    ),
    {
      content: "Create a new contact",
      trigger: ".o_control_panel_main_buttons .o-kanban-button-new",
      run: "click",
    },
    {
      content: "The donor is an individual, not a company",
      trigger: ".o_field_widget[name=company_type] input[data-value=person]",
      run: "click",
    },
    {
      content: "Set the first name of the new donor",
      trigger: ".o_field_widget[name=firstname] input",
      run: "edit John",
    },
    {
      content: "Set the last name of the new donor",
      trigger: ".o_field_widget[name=lastname]:visible input",
      run: `edit ${DONOR_LASTNAME}`,
    },
    {
      content: "Set the email of the new donor",
      trigger: ".o_field_widget[name=email] input",
      run: "edit john.doe@example.org",
    },
    ...stepUtils.saveForm(),
    stepUtils.autoExpandMoreButtons(),
    {
      content: "Open the invoices of the donor, which has none yet",
      trigger: "button[name=action_view_partner_invoices]",
      run: "click",
    },
    {
      content: "Create the invoice of the first donation",
      trigger: ".o_control_panel_main_buttons .o_list_button_add",
      run: "click",
    },
    {
      content: "The invoice is addressed to the new donor",
      trigger: `div[name=partner_id] input:value(${DONOR_LASTNAME})`,
    },
    {
      content: "Add a donation line",
      trigger: "div[name=invoice_line_ids] .o_field_x2many_list_row_add a",
      run: "click",
    },
    {
      content: "Look for the donation product",
      trigger: "div[name=invoice_line_ids] div[name=product_id] input",
      run: `edit ${DONATION_PRODUCT}`,
    },
    {
      content: "Select the donation product",
      trigger: `.ui-menu-item a:contains(${DONATION_PRODUCT})`,
      run: "click",
    },
    {
      content: "Open the amount cell of the donation line",
      trigger: "div[name=invoice_line_ids] td[name=price_unit]",
      run: "click",
    },
    {
      content: "Set the amount of the donation",
      trigger: "div[name=invoice_line_ids] div[name=price_unit] input",
      run: "edit 150",
    },
    ...stepUtils.saveForm(),
    {
      content: "Confirm the donation invoice",
      trigger: "button[name=action_post]",
      run: "click",
    },
    {
      content: "Register the payment of the donation",
      trigger: "button[name=action_register_payment]:visible",
      run: "click",
    },
    {
      content: "Create the payment",
      trigger: ".modal button[name=action_create_payments]:visible",
      run: "click",
    },
    {
      content: "The donation is paid, which queues the thank you letter",
      trigger: ".ribbon:contains(Paid)",
      async run() {
        // The thank you letter is generated by a queued job, which the
        // cron picks up. Run it now instead of waiting.
        await rpc("/web/dataset/call_kw", {
          model: "queue.job.replacement",
          method: "cron_run_jobs",
          args: [[]],
          kwargs: {},
        });

        // Check if we correctly generated the letter.
        const failed = await rpc("/web/dataset/call_kw", {
          model: "queue.job.replacement",
          method: "search_read",
          args: [[["state", "=", "failed"]], ["job_function", "job_result"]],
          kwargs: {},
        });
        if (failed.length) {
          throw new Error(
            "Queued job(s) failed:\n" +
              failed
                .map((j) => `${j.job_function}: ${j.job_result}`)
                .join("\n"),
          );
        }
      },
    },
    {
      content: "Refresh the invoice to see the generated thank you letter",
      trigger: ".ribbon:contains(Paid)",
      run: () => window.location.reload(),
      expectUnloadPage: true,
    },
    {
      content: "The thank you letter is generated and visible on the invoice",
      trigger: ".o_field_widget[name=communication_id] a.o_form_uri",
      run: "click",
    },
    {
      content: "Choose to send the letter by e-mail",
      trigger: ".o_field_widget[name=send_mode] select",
      run: "selectByLabel By e-mail",
    },
    {
      isActive: [".o-mail-Activity-markDone"],
      content: "Mark the scheduled call as done",
      trigger: ".o-mail-Activity-markDone",
      run: "click",
    },
    {
      isActive: [".o-mail-Activity-markDone"],
      content: "Confirm the call was made",
      trigger: ".o-mail-ActivityMarkAsDone button[aria-label=Done]",
      run: "click",
    },
    {
      content: "Send the thank you letter to the donor",
      trigger: "button[name=send]:visible",
      run: "click",
    },
    {
      content: "The thank you letter has been sent",
      trigger:
        `.o_data_row:contains(${DONOR_LASTNAME}) ` +
        "td[name=state]:contains(Done)",
    },
    ...goToDonor(),
    {
      content: "The new donor onboarding has started",
      trigger:
        ".o_field_widget[name=onboarding_new_donor_start_date] " +
        "input:not(:value(''))",
    },
    ...generateCommunication(FIRST_BLOG_POST),
    ...generateCommunication(SECOND_BLOG_POST),
  ],
});
