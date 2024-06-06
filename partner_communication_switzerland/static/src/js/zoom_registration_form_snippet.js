odoo.define("partner_communication_switzerland.zoom_form_snippet", function (
  require
) {
  "use strict";

  var core = require("web.core");
  var FormEditorRegistry = require("website_form.form_editor_registry");

  var _t = core._t;

  FormEditorRegistry.add("zoom_registration", {
    formFields: [
      {
        type: "char",
        modelRequired: true,
        name: "partner_firstname",
        string: _t("Firstname"),
      },
      {
        type: "char",
        modelRequired: true,
        name: "partner_lastname",
        string: _t("Lastname"),
      },
      {
        type: "char",
        modelRequired: true,
        name: "partner_email",
        string: _t("Email"),
      },
      {
        type: "char",
        modelRequired: false,
        name: "partner_phone",
        string: _t("Phone"),
      },
      {
        type: "boolean",
        modelRequired: false,
        name: "inform_me_for_next_zoom",
        string: _t("I am not available"),
      },
      {
        type: "char",
        modelRequired: false,
        name: "optional_message",
        string: _t("Optional message"),
      },
      {
        type: "boolean",
        modelRequired: false,
        name: "match_update",
        string: "Match Update",
      },
    ],
  });
});
