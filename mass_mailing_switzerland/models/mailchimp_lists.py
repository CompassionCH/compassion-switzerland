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

    @api.multi
    def members_cleaning_cron(self):
        """
        Cron used to clean mailchimp list of members. Mailchimp might store contact information
        to members no longer used in odoo. This cron archive them.
        :return:
        """

        # The cron should be launched on a weekly basis. So we can reduce the scope of the
        # query by request members modified in the last 2 weeks (2 weeks for safety)
        today = date.today()
        two_weeks_ago = today - timedelta(weeks=2)

        params = {
            "count": 1000,
            "since_last_changed": two_weeks_ago.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        }

        for mailchimp_list in self.search([("account_id", "!=", "False")]):

            response = mailchimp_list.account_id._send_request("lists/%s/members" % mailchimp_list.list_id, {},
                                                               method="GET", params=params)

            # get the list of members from odoo attached to this mailchimp list
            list_member_in_odoo = self.env["mail.mass_mailing.list_contact_rel"] \
                .search([("mailchimp_list_id.id", "=", mailchimp_list.id)])

            # based on mailchimp response look for members with no odoo reference
            to_rm_from_mailchimp = [member for member in response["members"]
                                    if str(member["web_id"]) not in list_member_in_odoo.mapped("mailchimp_id")]

            # archive all previously found members
            for member in to_rm_from_mailchimp:
                response = mailchimp_list.account_id._send_request(
                    "lists/%s/members/%s" % (mailchimp_list.list_id, member["id"]), {},
                    method="DELETE")

        return True
