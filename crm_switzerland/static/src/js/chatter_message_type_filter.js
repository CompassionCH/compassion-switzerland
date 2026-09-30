/** @odoo-module */

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { CheckboxItem } from "@web/core/dropdown/checkbox_item";
import { Thread } from "@mail/core/common/thread";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";

// Lets users choose which message_type(s) to show in the chatter (T3482):
// system-generated messages (stage changes, field tracking, ...) can't be
// deleted in v18 and pile up as clutter, so "System Notifications" is
// unchecked (hidden) by default; everything else stays visible. The choice
// is remembered per browser, not per user.
const STORAGE_KEY = "mail.visibleMessageTypes";

export const MESSAGE_TYPE_LABELS = {
  comment: _t("Comments & Notes"),
  email: _t("Incoming Emails"),
  email_outgoing: _t("Outgoing Emails"),
  notification: _t("System Notifications"),
  auto_comment: _t("Automated Notifications"),
  user_notification: _t("User Notifications"),
};

const DEFAULT_VISIBLE_MESSAGE_TYPES = {
  comment: true,
  email: true,
  email_outgoing: true,
  notification: false,
  auto_comment: true,
  user_notification: true,
};

function loadVisibleMessageTypes() {
  try {
    return {
      ...DEFAULT_VISIBLE_MESSAGE_TYPES,
      ...JSON.parse(browser.localStorage.getItem(STORAGE_KEY)),
    };
  } catch {
    return { ...DEFAULT_VISIBLE_MESSAGE_TYPES };
  }
}

Object.assign(Chatter.components, { CheckboxItem });

patch(Chatter.prototype, {
  setup() {
    super.setup(...arguments);
    this.messageTypeFilterDropdown = useDropdownState();
    this.state.visibleMessageTypes = loadVisibleMessageTypes();
  },
  get messageTypeLabels() {
    return MESSAGE_TYPE_LABELS;
  },
  onToggleMessageTypeVisible(messageType) {
    this.state.visibleMessageTypes[messageType] =
      !this.state.visibleMessageTypes[messageType];
    browser.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(this.state.visibleMessageTypes),
    );
  },
});

Thread.props.push("visibleMessageTypes?");
Object.assign(Thread.defaultProps, { visibleMessageTypes: null });

patch(Thread.prototype, {
  get orderedMessages() {
    const messages = super.orderedMessages;
    if (!this.props.visibleMessageTypes) {
      return messages;
    }
    return messages.filter(
      (message) => this.props.visibleMessageTypes[message.message_type] ?? true,
    );
  },
});
