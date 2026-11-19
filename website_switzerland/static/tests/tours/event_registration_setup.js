/**
 * End to end test of the setup of a Compassion event that is open to
 * registrations. A new event is created from the calendar, opened to
 * registrations with a fee, and its website page is checked before and after
 * the registrations are announced.
 *
 */
import { animationFrame, hover, pointerDown, pointerUp } from "@odoo/hoot-dom";
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const EVENT_NAME = `Tour Group Visit ${Date.now().toString(36)}`;
const REGISTRATION_TEMPLATE = "Group visit";
const REGISTRATION_PRODUCT = "EVENT_REG";
const REGISTRATION_FEE = "250";

const selectDays = async (fromDay, toDay) => {
  await pointerDown(fromDay);
  await animationFrame();
  await hover(toDay);
  await animationFrame();
  await pointerUp(toDay);
  await animationFrame();
};

const nextMonthDay = (day) => {
  const date = new Date();
  date.setDate(1);
  date.setMonth(date.getMonth() + 1);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const paddedDay = String(day).padStart(2, "0");
  return `.fc-daygrid-day[data-date="${date.getFullYear()}-${month}-${paddedDay}"]`;
};

const goBackToEvent = () => [
  {
    content: "Go back to the Compassion event",
    trigger: ".o_action_manager",
    run: () => window.history.back(),
  },
  {
    content: "The Compassion event is displayed again",
    trigger: ".o_form_view button[name=allocate_children_action]",
  },
  stepUtils.autoExpandMoreButtons(),
];

registry.category("web_tour.tours").add("event_registration_setup", {
  url: "/odoo",
  steps: () => [
    ...stepUtils.goToAppSteps("event.event_main_menu", "Open the Events app"),
    {
      content: "Open the Compassion events",
      trigger:
        '.o_nav_entry[data-menu-xmlid="crm_compassion.menu_events_compassion"]',
      run: "click",
    },
    {
      content: "Look at the next month, so that the event takes place later",
      trigger: ".o_calendar_button_next",
      run: "click",
    },
    {
      content: "Select the dates of the new event in the calendar",
      trigger: nextMonthDay(2),
      run() {
        return selectDays(this.anchor, nextMonthDay(4));
      },
    },
    {
      content: "Name the new event",
      trigger: ".o-calendar-quick-create--input",
      run: `edit ${EVENT_NAME}`,
    },
    {
      content: "Enter the details of the event",
      trigger: ".o-calendar-quick-create--edit-btn",
      run: "click",
    },
    {
      content: "Look for the registration template",
      trigger: ".o_form_view div[name=event_type_id] input",
      run: `edit ${REGISTRATION_TEMPLATE}`,
    },
    {
      content: `Select the ${REGISTRATION_TEMPLATE} registration template`,
      trigger: `.ui-menu-item a:contains(${REGISTRATION_TEMPLATE})`,
      run: "click",
    },
    ...stepUtils.saveForm(),
    {
      content: "Open the event to registrations",
      trigger: "button[name=open_registrations]",
      run: "click",
    },
    {
      content: "Set the registration fee",
      trigger: ".modal div[name=registration_fee] input",
      run: `edit ${REGISTRATION_FEE} && press Tab`,
    },
    {
      content: "Look for the registration product",
      trigger: ".modal div[name=product_id] input",
      run: "edit Event Registration",
    },
    {
      content: "Select the event registration product",
      trigger: `.ui-menu-item a:contains(${REGISTRATION_PRODUCT})`,
      run: "click",
    },
    {
      content: "Confirm the opening of the registrations",
      trigger: ".modal button[name=open_event]",
      run: "click",
    },
    {
      content: "The registrations are now handled by an Odoo event",
      trigger: `.o_form_view .o_statusbar_status button:contains(Announced)`,
    },
    ...goBackToEvent(),
    {
      content: "Open the page of the event on the website",
      trigger: ".o_field_widget[name=website_published] button",
      run: "click",
    },
    {
      content: "The event page is displayed on the website",
      trigger: ".o_website_preview :iframe div[name=dates_container]",
      timeout: 30000,
    },
    {
      content: "The page does not offer to register yet",
      trigger:
        ".o_website_preview :iframe #wrap:not(:has(#event_registration_section))",
    },
    ...goBackToEvent(),
    {
      content: "Open the registration process of the event",
      trigger: "button[name=manage_event_registration]",
      run: "click",
    },
    {
      content: "The registrations of the event are not announced yet",
      trigger:
        ".o_statusbar_status button.o_arrow_button_current:not(:contains(Announced))",
    },
    {
      content: "Announce the registrations of the event",
      trigger: ".o_statusbar_status button:contains(Announced)",
      run: "click",
    },
    {
      content: "The registrations of the event are announced",
      trigger:
        ".o_statusbar_status button.o_arrow_button_current:contains(Announced)",
    },
    ...goBackToEvent(),
    {
      content: "Open the page of the event on the website again",
      trigger: ".o_field_widget[name=website_published] button",
      run: "click",
    },
    {
      content: "The website now shows the registration form",
      trigger:
        ".o_website_preview :iframe #event_registration_section form#event_registration_form",
      timeout: 30000,
    },
  ],
});
