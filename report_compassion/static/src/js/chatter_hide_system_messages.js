/** @odoo-module */

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { Thread } from "@mail/core/common/thread";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";

// System-generated messages (stage changes, field tracking, ...) are
// message_type "notification"; hidden by default to keep the chatter
// readable, with a topbar toggle (see chatter_hide_system_messages.xml) to
// reveal them. The choice is remembered per browser, not per user (T3482).
const STORAGE_KEY = "mail.hideSystemMessages";

patch(Chatter.prototype, {
  setup() {
    super.setup(...arguments);
    Object.assign(this.state, {
      hideSystemMessages: browser.localStorage.getItem(STORAGE_KEY) !== "false",
    });
  },
  onClickToggleSystemMessages() {
    this.state.hideSystemMessages = !this.state.hideSystemMessages;
    browser.localStorage.setItem(STORAGE_KEY, this.state.hideSystemMessages);
  },
});

Thread.props.push("hideSystemMessages?");
Object.assign(Thread.defaultProps, { hideSystemMessages: false });

patch(Thread.prototype, {
  get orderedMessages() {
    const messages = super.orderedMessages;
    if (!this.props.hideSystemMessages) {
      return messages;
    }
    return messages.filter(
      (message) => message.message_type !== "notification",
    );
  },
});
