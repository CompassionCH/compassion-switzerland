/** @odoo-module */

import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";

// Log notes are internal and never sent by email: the branded signature
// rendered by ResUsers._compute_signature() (report_compassion/models/res_users.py)
// only makes sense on outgoing messages, so skip it when logging a note.
patch(Composer.prototype, {
  formatDefaultBodyForFullComposer(defaultBody, signature = "") {
    const keptSignature = this.props.type === "note" ? "" : signature;
    return super.formatDefaultBodyForFullComposer(defaultBody, keptSignature);
  },
});
