/**
 * End to end test of the sponsorship onboarding process. A brand new sponsor
 * takes a child in charge, pays the first invoice of the sponsorship, and both
 * the sponsor and the commitment are declared to GMC.
 */
import {
  QUEUE_TIMEOUT,
  openMenu,
  reloadStep,
  runQueuedJobs,
  searchFor,
} from "./tour_helpers";
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const SPONSOR_FIRSTNAME = "Marie";
const SPONSOR_LASTNAME = "Doe";
const SPONSOR_EMAIL = "marie.doe@example.org";
const CHILD_LOCAL_ID = "TR098765432";
const ORIGIN = "Sponsorship Creation Tour";
const MEDIUM = "Post";
const PAYMENT_MODE = "Permanent Order";
const WELCOME_COMMUNICATION =
  "Sponsorship Onboarding - Welcome and payment information";
const PHOTO_COMMUNICATION = "Sponsorship Onboarding - Photo by post";

const WAIT = 4000;

const goToSponsorships = (description) => [
  ...openMenu({
    app: "child_compassion.menu_sponsorship_root",
    section: "child_compassion.menu_sponsorship_section",
    item: "sponsorship_compassion.menu_sponsorship_contract_form",
    description,
  }),
  {
    content: "Wait for the list of sponsorships",
    trigger: ".o_list_view th[data-name=activation_date]",
  },
];

const goToSponsorship = () => [
  ...goToSponsorships("Back to the Sponsorship app"),
  ...searchFor(SPONSOR_LASTNAME),
  {
    content: "Open the sponsorship",
    trigger: `.o_data_row td[name=partner_id]:contains(${SPONSOR_LASTNAME})`,
    run: "click",
  },
];

/**
 * Sends one of the outgoing GMC messages of the new sponsor from the Message
 * Center, and waits for the answer of GMC.
 *
 * @param {String} action name of the GMC action of the message to send.
 * @param {String} menu xmlid of the Message Center menu listing it.
 */
const sendGmcMessage = (action, menu) => [
  ...openMenu({
    app: "message_center_compassion.menu_message_center",
    section: "message_center_compassion.menu_message_outgoing",
    item: menu,
    description: "Open the Message Center",
  }),
  {
    content: "Wait for the outgoing messages",
    trigger: ".o_list_view .o_group_header, .o_list_view .o_data_row",
  },
  {
    isActive: [`.o_group_header:contains(${action})`],
    content: `Expand the ${action} messages`,
    trigger: `.o_group_header:contains(${action})`,
    run: "click",
  },
  {
    content: `Open the ${action} message of the new sponsor`,
    trigger:
      `.o_data_row:contains(${action}) ` +
      `td[name=partner_id]:contains(${SPONSOR_LASTNAME})`,
    run: "click",
  },
  {
    content: `The ${action} message was not sent to GMC yet`,
    trigger:
      ".o_statusbar_status button[data-value=new].o_arrow_button_current",
  },
  {
    content: `Send the ${action} message to GMC`,
    trigger: "button[name=process_messages]",
    run: "click",
  },
  {
    content: "The message left the pool",
    trigger:
      ".o_statusbar_status button[data-value=new]:not(.o_arrow_button_current)",
  },
  {
    content: "Let the queue hand the message over to GMC",
    trigger: ".o_form_view",
    timeout: QUEUE_TIMEOUT,
    async run() {
      await runQueuedJobs();
    },
  },
  reloadStep("Refresh the message to see the answer of GMC"),
  {
    content: `GMC accepted the ${action} message`,
    trigger:
      ".o_statusbar_status button[data-value=success].o_arrow_button_current",
  },
];

registry.category("web_tour.tours").add("create_a_sponsorship", {
  url: "/odoo",
  steps: () => [
    ...goToSponsorships("Open the Sponsorship app"),
    {
      content: "Create a new sponsorship",
      trigger: ".o_control_panel_main_buttons .o_list_button_add",
      run: "click",
    },
    {
      content: "Look for a sponsor that does not exist yet",
      trigger: ".o_field_widget[name=partner_id] input",
      run: `edit ${SPONSOR_LASTNAME}`,
    },
    {
      content: "Create the new sponsor",
      trigger:
        ".o_field_widget[name=partner_id] " +
        ".o_m2o_dropdown_option_create_edit a",
      run: "click",
    },
    {
      content: "Set the first name of the new sponsor",
      trigger: ".modal .o_field_widget[name=firstname] input",
      run: `edit ${SPONSOR_FIRSTNAME}`,
    },
    {
      content: "Set the last name of the new sponsor",
      trigger: ".modal .o_field_widget[name=lastname]:visible input",
      run: `edit ${SPONSOR_LASTNAME}`,
    },
    {
      content: "Set the e-mail of the new sponsor",
      trigger: ".modal .o_field_widget[name=email] input",
      run: `edit ${SPONSOR_EMAIL}`,
    },
    {
      content: "Save the new sponsor",
      trigger: ".modal .modal-footer .o_form_button_save",
      run: "click",
    },
    {
      content: "The sponsorship is registered on the new sponsor",
      trigger: `.o_field_widget[name=partner_id] input:value(${SPONSOR_LASTNAME})`,
    },
    {
      content: "Look for the consigned child",
      trigger: ".o_field_widget[name=child_id] input",
      run: `edit ${CHILD_LOCAL_ID}`,
    },
    {
      content: "Select the consigned child",
      trigger: `.o-autocomplete--dropdown-item a:contains(${CHILD_LOCAL_ID})`,
      run: "click",
    },
    {
      content: "Look for payment options, the sponsor has none yet",
      trigger: ".o_field_widget[name=group_id] input",
      run: "edit Onboarding payment options",
    },
    {
      content: "Create the payment options",
      trigger:
        ".o_field_widget[name=group_id] .o_m2o_dropdown_option_create_edit a",
      run: "click",
    },
    {
      content: "Look for the payment mode",
      trigger: ".modal .o_field_widget[name=payment_mode_id] input",
      run: `edit ${PAYMENT_MODE}`,
    },
    {
      content: `Pay the sponsorship by ${PAYMENT_MODE}`,
      trigger: `.modal .o-autocomplete--dropdown-item a:contains(${PAYMENT_MODE})`,
      run: "click",
    },
    {
      content: "Save the payment options",
      trigger: ".modal .modal-footer .o_form_button_save",
      run: "click",
    },
    {
      content: "Look for the origin of the sponsorship",
      trigger: ".o_field_widget[name=origin_id] input",
      run: `edit ${ORIGIN}`,
    },
    {
      content: "Select the origin of the sponsorship",
      trigger: `.o-autocomplete--dropdown-item a:contains(${ORIGIN})`,
      run: "click",
    },
    {
      content: "Look for the medium of the sponsorship",
      trigger: ".o_field_widget[name=medium_id] input",
      run: `edit ${MEDIUM}`,
    },
    {
      content: "Select the medium of the sponsorship",
      trigger: `.o-autocomplete--dropdown-item a:contains(${MEDIUM})`,
      run: "click",
    },
    ...stepUtils.saveForm(),
    {
      content: "Validate the sponsorship",
      trigger: "button[name=contract_waiting]",
      run: "click",
    },
    {
      content: "The sponsorship waits for its first payment",
      trigger:
        ".o_statusbar_status button[data-value=waiting].o_arrow_button_current",
    },
    {
      content: "The sponsorship has a start date",
      trigger: ".o_field_widget[name=start_date] span:not(:empty)",
      timeout: QUEUE_TIMEOUT,
      async run() {
        await runQueuedJobs(WAIT);
      },
    },
    reloadStep("Refresh the sponsorship to see the generated invoices"),
    {
      content: "Open the invoices of the sponsorship",
      trigger: "button[name=open_invoices]",
      run: "click",
    },
    {
      content: "Open the first invoice, issued on the 1st of the month",
      trigger: ".o_list_view .o_data_row:first td[name=status_in_payment]",
      run: "click",
    },
    {
      content: "Register the payment of the first invoice",
      trigger: "button[name=action_register_payment]:visible",
      run: "click",
    },
    {
      content: "Create the payment",
      trigger: ".modal button[name=action_create_payments]:visible",
      run: "click",
    },
    {
      content: "The first invoice is paid, which activates the sponsorship",
      trigger: ".ribbon:contains(Paid)",
      timeout: QUEUE_TIMEOUT,
      async run() {
        await runQueuedJobs();
      },
    },
    ...goToSponsorship(),
    {
      content: "The sponsorship is now active",
      trigger:
        ".o_statusbar_status button[data-value=active].o_arrow_button_current",
    },
    {
      content: "The sponsorship has an activation date",
      trigger: ".o_field_widget[name=activation_date] span:not(:empty)",
    },
    {
      content: "Open the sponsor of the sponsorship",
      trigger: ".o_field_widget[name=partner_id] a.o_form_uri",
      run: "click",
    },
    {
      content: "The new sponsor got the Sponsor tag",
      trigger: ".o_field_widget[name=category_id] .o_tag:contains(Sponsor)",
    },
    stepUtils.autoExpandMoreButtons(),
    {
      content: "Open the communications of the new sponsor",
      trigger: ".o-form-buttonbox button:has(span:contains(Communications))",
      run: "click",
    },
    {
      content: "Wait for the communications of the sponsor",
      trigger: ".o_list_view th[data-name=config_id]",
    },
    {
      content: `The ${WELCOME_COMMUNICATION} is ready to be sent`,
      trigger:
        `.o_data_row:contains(${WELCOME_COMMUNICATION}) ` +
        "td[name=state]:contains(Pending)",
    },
    {
      content: `The ${PHOTO_COMMUNICATION} is ready to be sent`,
      trigger:
        `.o_data_row:contains(${PHOTO_COMMUNICATION}) ` +
        "td[name=state]:contains(Pending)",
    },
    ...sendGmcMessage(
      "UpsertPartner",
      "sponsorship_compassion.menu_message_partner",
    ),
    ...sendGmcMessage(
      "UpsertSponsorship",
      "sponsorship_compassion.menu_message_sponsorship",
    ),
    ...goToSponsorship(),
    {
      content: "The sponsorship received its global ID from GMC",
      trigger: ".o_field_widget[name=gmc_commitment_id] span:not(:empty)",
    },
  ],
});
