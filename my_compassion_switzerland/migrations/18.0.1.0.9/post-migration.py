##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade

# eBill is activated, not subscribed to. A module update does not overwrite
# translations already stored, so the two German terms are replaced here.
NEW_TERMS = {
    "ebill_postfinance_recipient_subscription.subscribe_template_content": {
        "Subscribe to E-Bill": "eBill aktivieren",
    },
    "ebill_postfinance_recipient_subscription.success_template_content": {
        "You have successfully subscribed to E-Bill.": (
            "Du hast eBill erfolgreich aktiviert."
        ),
    },
}


@openupgrade.migrate()
def migrate(env, version):
    for xmlid, terms in NEW_TERMS.items():
        view = env.ref(xmlid, raise_if_not_found=False)
        if view:
            view.update_field_translations("arch_db", {"de_DE": terms})
