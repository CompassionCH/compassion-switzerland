import {
  QUEUE_TIMEOUT,
  WAIT,
  goToSponsorships,
  runQueuedJobs,
} from "./tour_helpers";
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const SPONSOR_FIRSTNAME = "Jane";
const SPONSOR_LASTNAME = "Doe";
const SPONSOR_NAME = `${SPONSOR_FIRSTNAME} ${SPONSOR_LASTNAME}`;
const SPONSOR_EMAIL = "Jane.doe@example.org";
const CHILD_LOCAL_ID = "TR087654321";
const ORIGIN = "Write and Pray Tour";
const MEDIUM = "Post";
const TYPE = "Write&Pray";
const WELCOME_COMMUNICATION = "Write&Pray Onboarding - Welcome";
const PHOTO_COMMUNICATION = "Sponsorship Onboarding - Photo by post";

const totalIsFree = (content) => ({
  content,
  trigger: "div[name=total_amount]:contains(/^0\\.00$/)",
});

registry.category("web_tour.tours").add("write_and_pray_sponsorship", {
  url: "/odoo",
  steps: () => [
    ...goToSponsorships("Open the Sponsorship app"),
    {
      content: "Create a new sponsorship",
      trigger: ".o_control_panel_main_buttons .o_list_button_add",
      run: "click",
    },
    {
      content: `Make it a ${TYPE} sponsorship`,
      trigger: ".o_field_widget[name=type] select",
      run: `selectByLabel ${TYPE}`,
    },
    {
      content: "Acknowledge the warning about the unknown correspondent",
      trigger: ".modal .o_error_dialog .o-default-button",
      run: "click",
    },
    totalIsFree(`A ${TYPE} sponsorship is free of charge`),
    {
      content: "Look for the child on hold",
      trigger: ".o_field_widget[name=child_id] input",
      run: `edit ${CHILD_LOCAL_ID}`,
    },
    {
      content: "Select the child on hold",
      trigger: `.o-autocomplete--dropdown-item a:contains(${CHILD_LOCAL_ID})`,
      run: "click",
    },
    {
      content: "Look for the sponsor by their e-mail",
      trigger: ".o_field_widget[name=partner_id] input",
      run: `edit ${SPONSOR_EMAIL}`,
    },
    {
      content: "Select the only partner holding that e-mail",
      trigger:
        ".o_field_widget[name=partner_id] " +
        ".o-autocomplete--dropdown-item:not(.o_m2o_dropdown_option) " +
        `a:contains(${SPONSOR_NAME})`,
      run: "click",
    },
    {
      content: "The sponsorship is registered on the sponsor",
      trigger: `.o_field_widget[name=partner_id] input:value(${SPONSOR_LASTNAME})`,
    },
    {
      content: "The payment options of the sponsor are picked up",
      trigger: ".o_field_widget[name=group_id] input:not(:value(''))",
    },
    totalIsFree("Naming the payer did not put a price on the sponsorship"),
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
    totalIsFree(`The saved ${TYPE} sponsorship still costs nothing`),
    {
      content: "Validate the sponsorship",
      trigger: "button[name=contract_waiting]",
      run: "click",
    },
    {
      content: "Nothing is due, so the sponsorship is active right away",
      trigger:
        ".o_statusbar_status button[data-value=active].o_arrow_button_current",
    },
    {
      content: "The sponsorship has an activation date",
      trigger: ".o_field_widget[name=activation_date] span:not(:empty)",
      timeout: QUEUE_TIMEOUT,
      async run() {
        await runQueuedJobs(WAIT);
      },
    },
    {
      content: "Open the sponsor of the sponsorship",
      trigger: ".o_field_widget[name=partner_id] a.o_form_uri",
      run: "click",
    },
    stepUtils.autoExpandMoreButtons(),
    {
      content: "Open the communications of the sponsor",
      trigger: ".o-form-buttonbox button:has(span:contains(Communications))",
      run: "click",
    },
    {
      content: "Wait for the communications of the sponsor",
      trigger: ".o_list_view th[data-name=config_id]",
    },
    {
      content: `The ${WELCOME_COMMUNICATION} is sent by SMS`,
      trigger:
        `.o_data_row:contains(${WELCOME_COMMUNICATION}) ` +
        "td[name=send_mode]:contains(SMS)",
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
  ],
});
