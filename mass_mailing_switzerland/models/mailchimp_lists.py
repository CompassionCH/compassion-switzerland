##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, _


class MailchimpLists(models.Model):
    _inherit = "mailchimp.lists"

    def process_member_from_stored_response(self, pending_record):
        # Avoid loops in mailchimp sync
        out = super(MailchimpLists,
                    self.with_context(import_from_mailchimp=True)
                    ).process_member_from_stored_response(pending_record)

        # mailing_contact with invalid_email should be unlinked from res.partner
        invalid_contacts = self.env['mail.mass_mailing.contact'].search([('is_email_valid', '=', False)])

        for invalid_contact in invalid_contacts:

            ref_partner = self.env['res.partner'].search([('id', '=', invalid_contact.partner_id.id)])
            if ref_partner:
                vals = {
                    "invalid_mail": invalid_contact.email,
                    "email": False
                }
                ref_partner.with_context(recompute=False).write(vals)

                # inform partner email is not valid trough a prepared communication
                invalid_comm = self.env.ref("partner_communication_switzerland.wrong_email")
                if ref_partner.id:
                    self.env["partner.communication.job"].create(
                        {
                            "config_id": invalid_comm.id,
                            "partner_id": ref_partner.id,
                            "object_ids": ref_partner.id,
                        }
                    )
                ref_partner.message_post(
                    body=_("The email couldn't be sent due to invalid address"),
                    subject=ref_partner.invalid_mail
                )
            else:
                # if reference on partner is not there but mailing contact still exist remove mailing contact
                invalid_contact.unlink()
        return out
