##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, _
from datetime import date, timedelta


class MailchimpLists(models.Model):
    _inherit = "mailchimp.lists"

    def process_member_from_stored_response(self, pending_record):
        # Avoid loops in mailchimp sync
        return super(MailchimpLists,
                     self.with_context(import_from_mailchimp=True)
                     ).process_member_from_stored_response(pending_record)

    @api.multi
    def get_mapped_merge_field(self):
        res = super().get_mapped_merge_field()
        res.extend([
            "lastname", "firstname", "number_sponsorships", "opt_out", "category_id"])
        return res
