/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { createDocumentFragmentFromContent } from "@mail/utils/common/html";
import { messageActionsRegistry } from "@mail/core/common/message_actions";
import { toRaw } from "@odoo/owl";

// The core "edit" action flattens the message body to plain text
// (convertBrToLineBreak) and edits it in a textarea, which destroys any
// formatting a log note was written with in the full composer. This extra
// action reopens the Wysiwyg full composer on the original HTML instead, and
// updates the existing message rather than posting a new one (see
// report_compassion/wizards/mail_compose_message.py).
messageActionsRegistry.add("edit-note-full", {
  condition: (component) =>
    component.props.message.editable && component.props.message.is_note,
  icon: "fa fa-pencil-square-o",
  title: _t("Edit in full composer"),
  onClick: (component) => {
    const message = toRaw(component.props.message);
    const doc = createDocumentFragmentFromContent(message.body);
    // Core stamps this marker into the body on every update: keep it out of the
    // editable content so it neither shows up in the editor nor piles up.
    doc.querySelectorAll(".o-mail-Message-edited").forEach((el) => el.remove());
    return component.env.services.action.doAction({
      name: _t("Edit log note"),
      type: "ir.actions.act_window",
      res_model: "mail.compose.message",
      view_mode: "form",
      views: [[false, "form"]],
      target: "new",
      context: {
        default_body: doc.body.innerHTML,
        default_edit_message_id: message.id,
        default_email_add_signature: false,
        default_model: message.thread.model,
        default_res_ids: [message.thread.id],
        default_subtype_xmlid: "mail.mt_note",
        is_thread_composer: true,
      },
    });
  },
  sequence: 81,
});
