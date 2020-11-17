##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class MailchimpLists(models.Model):
    _inherit = "mailchimp.lists"

    def process_member_from_stored_response(self, pending_record):
        # Avoid loops in mailchimp sync
        return super(MailchimpLists,
                     self.with_context(import_from_mailchimp=True)
                     ).process_member_from_stored_response(pending_record)
