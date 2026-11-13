##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class RecurringContract(models.Model):
    _inherit = "recurring.contract"

    # Searchable link to the letters, used by the follow-up automation rules
    # (data/letter_followup_rules.xml) to find sponsorships without a child letter.
    correspondence_ids = fields.One2many(
        "correspondence", "sponsorship_id", string="Letters", readonly=True
    )
