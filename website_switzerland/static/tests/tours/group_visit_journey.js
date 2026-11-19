import { formatDate } from "@web/core/l10n/dates";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const { DateTime } = luxon;

const TOKEN_KEY = "group_visit_tour_token";

const urlToken = () => new URLSearchParams(location.search).get("tour_token");

const newToken = () => Math.random().toString(16).slice(2, 10);

const token = () => {
  const token_ = urlToken() || sessionStorage.getItem(TOKEN_KEY) || newToken();
  sessionStorage.setItem(TOKEN_KEY, token_);
  return token_;
};

const eventPage = async () => {
  if (document.querySelector("#event_registration_section form")) {
    return location.pathname;
  }
  const domain = [
    ["type", "=", "tour"],
    ["is_published", "=", true],
    ["end_date", ">=", DateTime.now().toISODate()],
    ["odoo_event_id.fundraising", "=", true],
  ];
  if (urlToken()) {
    domain.push(["name", "ilike", urlToken()]);
  }
  const callKw = (model, method, args, kwargs = {}) =>
    rpc(`/web/dataset/call_kw/${model}/${method}`, {
      model,
      method,
      args,
      kwargs,
    });
  const trips = await callKw("crm.event.compassion", "search_read", [domain], {
    fields: ["website_url", "odoo_event_id"],
    order: "start_date asc",
  });
  const events = trips.length
    ? await callKw(
        "event.event",
        "read",
        [trips.map((trip) => trip.odoo_event_id[0])],
        { fields: ["registration_open", "registration_full"] },
      )
    : [];
  const open = new Set(
    events
      .filter((event) => event.registration_open && !event.registration_full)
      .map((event) => event.id),
  );
  const trip = trips.find((trip) => open.has(trip.odoo_event_id[0]));
  if (!trip) {
    throw new Error(
      "No published group visit with a fundraising is open to registrations",
    );
  }
  return trip.website_url;
};

const participant = () => ({
  firstname: "Jane",
  lastname: `Doe${token()}`,
  email: `group.visit.${token()}@tour.example.org`,
  profileName: `Jane D. ${token()}`,
  motto: "I am going to meet my sponsored child!",
});

const BIRTHDATE = DateTime.fromISO("1985-04-23");
const PASSPORT_EXPIRATION = DateTime.now().plus({ years: 5 });
const PASSPORT_NUMBER = "X1234567";
const EMERGENCY_NAME = "Emergency Contact";
const EMERGENCY_PHONE = "+41 21 546 65 65";
const STREET = "Rue Galilee 3";
const ZIP = "1400";
const CITY = "Yverdon-les-Bains";

const PARTICIPANT_PASSWORD = "GroupVisitTour!42";

// Keep in sync with the fixture.
const MEDICAL_QUESTION = "Do you have a health issue we should know about";
const MEDICAL_ANSWER = "I have back problems";
const ALLERGY_QUESTION = "Tell us about your allergies";
const ALLERGY_ANSWER = "pollen";
const TRAVEL_DOCUMENTS = "Group visit: travel documents request";
const FEEDBACK_RATING = "Excellent";
const FEEDBACK_QUESTION = "Suggestions for improvement";
const FEEDBACK_ANSWER = "Nothing to improve, it was a life changing trip";

/**
 * A PNG large enough for the profile picture to pass the print resolution
 * check.
 */
const profilePicture = async () => {
  const canvas = document.createElement("canvas");
  canvas.width = 1280;
  canvas.height = 960;
  const context = canvas.getContext("2d");
  context.fillStyle = "#0054a6";
  context.fillRect(0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/png"),
  );
  return new File([blob], "participant.png", { type: "image/png" });
};

const document_ = (name) =>
  new File([`%PDF-1.4 ${name}`], `${name}.pdf`, { type: "application/pdf" });

const attach = (input, file) => {
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
};

const fill = (name, value, content) => ({
  content: content || `Fill in ${name}`,
  trigger: `#event_registration_form [name="${name}"]`,
  run: `edit ${value}`,
});

registry.category("web_tour.tours").add("group_visit_registration", {
  steps: () => {
    const { firstname, lastname, email, profileName, motto } = participant();
    return [
      {
        content: "Go to the page of the group visit",
        trigger: "body",
        async run() {
          const url = new URL(await eventPage(), location.origin);
          url.searchParams.set("tour_token", urlToken() || newToken());
          location.assign(url);
        },
        expectUnloadPage: true,
      },
      {
        content: "The event page offers to register",
        trigger: "#event_registration_section form#event_registration_form",
      },
      fill("partner_firstname", firstname),
      fill("partner_lastname", lastname),
      fill("partner_email", email),
      fill(
        "partner_birthdate_date",
        formatDate(BIRTHDATE),
        "Fill in the birthdate",
      ),
      fill("partner_phone", "+41 24 434 21 24"),
      fill("partner_street", STREET),
      fill("partner_zip", ZIP),
      fill("partner_city", CITY),
      fill(
        "birth_name",
        `${firstname} ${lastname}`,
        "Fill in the passport name",
      ),
      fill("passport_number", PASSPORT_NUMBER),
      fill(
        "passport_expiration_date",
        formatDate(PASSPORT_EXPIRATION),
        "Fill in the passport expiration date",
      ),
      fill("emergency_name", EMERGENCY_NAME),
      fill("emergency_phone", EMERGENCY_PHONE),
      {
        content: "Ask for a single room",
        trigger: "#event_registration_form input[name=single_room]",
        run: "click",
      },
      fill("profile_name", profileName, "Name the public profile"),
      {
        content: "Upload the picture of the public profile",
        trigger: "#event_registration_form input[name=profile_picture]",
        async run() {
          attach(this.anchor, await profilePicture());
        },
      },
      fill("ambassador_quote", motto, "Write the motto of the public profile"),
      {
        content: "Accept the legal terms",
        trigger: "#event_registration_form input[name=privacy_policy]",
        run: "click",
      },
      {
        content: "Send the registration",
        trigger: "#event_registration_form .s_website_form_send",
        run: "click",
        expectUnloadPage: true,
      },
      {
        content: "The registration was taken",
        trigger: "#wrap .fa-thumbs-up",
      },
    ];
  },
});

const openParticipant = () => [
  {
    content: "Open the sponsor trip the participant registered to",
    trigger: "body",
    async run() {
      const lastRegistration = async (email) => {
        const [registration] = await rpc(
          "/web/dataset/call_kw/event.registration/search_read",
          {
            model: "event.registration",
            method: "search_read",
            args: [[["email", "=like", email]]],
            kwargs: {
              fields: ["event_id", "email"],
              order: "id desc",
              limit: 1,
            },
          },
        );
        return registration;
      };
      const registration =
        (await lastRegistration(participant().email)) ||
        (await lastRegistration("group.visit.%@tour.example.org"));
      if (!registration) {
        throw new Error(
          `No registration of ${participant().email}, nor of any other tour`,
        );
      }
      const [, token_] = registration.email.match(/^group\.visit\.(.+)@/);
      sessionStorage.setItem(TOKEN_KEY, token_);
      location.assign(
        `/odoo/action-event.action_event_view/${registration.event_id[0]}`,
      );
    },
    expectUnloadPage: true,
  },
  {
    content: "Open the expected attendees of the trip",
    trigger: "button.oe_stat_button:has(div[name=seats_taken])",
    run: "click",
  },
  {
    content: "Open the participant",
    trigger: `.o_data_row:contains(${participant().lastname}) td[name=email]`,
    run: "click",
  },
];

registry.category("web_tour.tours").add("group_visit_confirmation", {
  steps: () => {
    const { firstname, email, profileName, motto } = participant();
    return [
      ...openParticipant(),
      {
        content: "The public profile of the participant was submitted",
        trigger: `.o_form_view div[name=profile_name] input:value(${profileName})`,
      },
      {
        content: "The motto of the participant was submitted",
        trigger: `.o_form_view div[name=ambassador_quote] textarea:value(${motto})`,
      },
      {
        content: "The travel information of the participant was submitted",
        trigger: `.o_form_view div[name=passport_number] input:value(${PASSPORT_NUMBER})`,
      },
      {
        content: "Focus the contact of the participant",
        trigger: ".o_form_view div[name=partner_id] input",
        run: "click",
      },
      {
        content: "Open the contact of the participant",
        trigger: ".o_form_view div[name=partner_id] button.o_external_button",
        run: "click",
      },
      {
        content: "The contact carries the name of the participant",
        trigger: `.o_form_view div[name=firstname] input:value(${firstname})`,
      },
      {
        content: "The contact carries the e-mail of the participant",
        trigger: `.o_form_view div[name=email] input:value(${email})`,
      },
      {
        content: "The contact carries the address of the participant",
        trigger: `.o_form_view div[name=street] input:value(${STREET})`,
      },
      {
        content: "Open the personal information of the contact",
        trigger: ".o_notebook a[name=personal_information_page]",
        run: "click",
      },
      {
        content: "The contact carries the birthdate of the participant",
        trigger: `.o_form_view div[name=birthdate_date] input:value(${formatDate(
          BIRTHDATE,
        )})`,
      },
      {
        content: "Go back to the registration",
        trigger: ".o_form_view div[name=firstname] input",
        run: () => window.history.back(),
      },
      {
        content: "The registration is confirmed",
        trigger: ".o_form_view div[name=state] :contains(Registered)",
      },
      {
        content: "The participant now waits for the down payment",
        trigger:
          ".o_statusbar_status button.o_arrow_button_current:contains(Down payment)",
      },
      {
        content: "Open the public profile of the participant",
        trigger: ".o_form_view div[name=is_published] button",
        run: "click",
      },
      {
        content: "The public profile shows the motto of the participant",
        trigger: `.o_website_preview :iframe figcaption:contains(${motto})`,
        timeout: 30000,
      },
      {
        content: "The public profile shows the picture of the participant",
        trigger: ".o_website_preview :iframe figure img.figure-img",
      },
      {
        content: "The public profile shows the fundraising of the participant",
        trigger: ".o_website_preview :iframe .progress .progress-amount",
      },
    ];
  },
});

const openTask = (name) => ({
  content: `Open the "${name}" task`,
  trigger: `[name=tasks_section] a:contains(${name})`,
  run: "click",
  expectUnloadPage: true,
});

const taskIsDone = (name) => ({
  content: `The "${name}" task is done`,
  trigger: `[name=tasks_section] a:contains(${name}) i.fa-check`,
});

const uploadDocument = (task, input, document) => [
  openTask(task),
  {
    content: `Upload the ${document}`,
    trigger: `#event_registration_form input[name=${input}]`,
    run() {
      attach(this.anchor, document_(document));
    },
  },
  {
    content: `Send the ${document}`,
    trigger: "#event_registration_form .s_website_form_send",
    run: "click",
    expectUnloadPage: true,
  },
  taskIsDone(task),
];

registry.category("web_tour.tours").add("group_visit_documents", {
  steps: () => [
    {
      content: "Choose the password of the new MyCompassion account",
      trigger: ".oe_signup_form input[name=password]",
      run: `edit ${PARTICIPANT_PASSWORD}`,
    },
    {
      content: "Confirm the password",
      trigger: ".oe_signup_form input[name=confirm_password]",
      run: `edit ${PARTICIPANT_PASSWORD}`,
    },
    {
      content: "Accept the legal terms of MyCompassion",
      trigger: ".oe_signup_form input[name=privacy_policy]",
      run: "click",
    },
    {
      content: "Activate the account",
      trigger: ".oe_signup_form button[type=submit]",
      run: "click",
      expectUnloadPage: true,
    },
    {
      content: "Open the trip from the MyCompassion home",
      trigger: "a[href^='/my/events']",
      run: "click",
      expectUnloadPage: true,
    },
    {
      content: "The trip lists what is left to do",
      trigger: "[name=tasks_section] h3",
    },
    openTask("Sign travel agreement"),
    {
      content: "Accept the terms of the travel agreement",
      trigger: "form[action='/my/events/travel_contract'] input[name=accept]",
      run: "click",
    },
    {
      content: "Sign the travel agreement",
      trigger: "form[action='/my/events/travel_contract'] button",
      run: "click",
      expectUnloadPage: true,
    },
    taskIsDone("Sign travel agreement"),
    openTask("Sign child protection agreement"),
    {
      content: "Read the code of conduct",
      trigger: "input[name=read_check]",
      run: "click",
    },
    {
      content: "Agree to abide by the code of conduct",
      trigger: "input[name=validation_check]",
      run: "click",
    },
    {
      content: "Agree to report any abuse",
      trigger: "input[name=legal_check]",
      run: "click",
    },
    {
      content: "Acknowledge the consequences of a breach",
      trigger: "input[name=understand_check]",
      run: "click",
    },
    {
      content: "Sign the child protection charter",
      trigger: "form .s_website_form_send",
      run: "click",
      expectUnloadPage: true,
    },
    {
      content: "Go back to the trip",
      trigger: "a[href^='/my/events/']",
      run: "click",
      expectUnloadPage: true,
    },
    taskIsDone("Sign child protection agreement"),
    ...uploadDocument("Send a passport copy", "passport", "passport"),
    ...uploadDocument(
      "Send certificate of criminal record",
      "criminal_record",
      "criminal-record",
    ),
    {
      content: "The agreements are behind, the medical survey is next",
      trigger: "[name=tasks_section] a:contains(Fill medical survey)",
    },
  ],
});

const chooseAnswer = (question, answer) => ({
  content: `Answer "${answer}" to "${question}"`,
  trigger:
    `.js_question-wrapper:has(h3:contains(${question}))` +
    ` label.o_survey_choice_btn:contains(${answer})`,
  run: "click",
});

const writeAnswer = (question, answer) => ({
  content: `Write the answer to "${question}"`,
  trigger: `.js_question-wrapper:has(h3:contains(${question})) textarea`,
  run: `edit ${answer}`,
});

const fillSurvey = (name, answers) => [
  {
    content: `Start the ${name}`,
    trigger: "button[value=start]",
    run: "click",
  },
  ...answers,
  {
    content: `Send the ${name}`,
    trigger: "button[value=finish]",
    run: "click",
  },
  {
    content: `The ${name} is filled`,
    trigger: ".o_survey_finished",
  },
];

registry.category("web_tour.tours").add("group_visit_medical_survey", {
  steps: () => [
    openTask("Fill medical survey"),
    ...fillSurvey("medical survey", [
      chooseAnswer(MEDICAL_QUESTION, MEDICAL_ANSWER),
      writeAnswer(ALLERGY_QUESTION, ALLERGY_ANSWER),
    ]),
  ],
});

registry.category("web_tour.tours").add("group_visit_trip_invoice", {
  steps: () => [
    ...openParticipant(),
    {
      content: "Open the medical discharge task",
      trigger:
        "div[name=task_ids] .o_data_row:contains(Sign medical discharge)" +
        " td[name=task_id]",
      run: "click",
    },
    {
      content: "Tick off the medical discharge",
      trigger:
        "div[name=task_ids] .o_data_row.o_selected_row .o_field_boolean input",
      run: "click",
    },
    ...stepUtils.saveForm(),
    {
      content: "The participant now owes the trip itself",
      trigger:
        ".o_statusbar_status button.o_arrow_button_current:contains(Payment)",
    },
    {
      content: "Invoice the trip to the participant",
      trigger: ".o_form_view button[name=create_trip_invoice]",
      run: "click",
    },
    {
      content: "The trip was invoiced, so it cannot be invoiced again",
      trigger: ".o_form_view:not(:has(button[name=create_trip_invoice]))",
    },
    {
      content: "Choose a communication to send to the participant",
      trigger: ".o_form_view button[name=button_send_reminder]",
      run: "click",
    },
    {
      content: "Look for the travel documents request",
      trigger: ".modal div[name=config_id] input",
      run: `edit ${TRAVEL_DOCUMENTS}`,
    },
    {
      content: "Select the travel documents request",
      trigger: `.ui-menu-item a:contains(${TRAVEL_DOCUMENTS})`,
      run: "click",
    },
    {
      content: "Prepare the travel documents request",
      trigger: ".modal button[name=button_open_mail_sender]",
      run: "click",
    },
    {
      content: "Send the travel documents request",
      trigger: ".modal button[name=send]",
      run: "click",
    },
    {
      content: "The participant received the travel documents request",
      trigger: ".o_form_view:not(:has(.modal))",
    },
  ],
});

registry.category("web_tour.tours").add("group_visit_feedback_survey", {
  steps: () =>
    fillSurvey("feedback survey", [
      {
        content: "Rate every part of the trip",
        trigger: `.js_question-wrapper label.o_survey_choice_btn:contains(${FEEDBACK_RATING})`,
        run() {
          for (const question of document.querySelectorAll(
            ".js_question-wrapper",
          )) {
            const choices = question.querySelectorAll(
              "label.o_survey_choice_btn",
            );
            const rating = [...choices].find((choice) =>
              choice.textContent.includes(FEEDBACK_RATING),
            );
            rating?.click();
          }
        },
      },
      writeAnswer(FEEDBACK_QUESTION, FEEDBACK_ANSWER),
    ]),
});
