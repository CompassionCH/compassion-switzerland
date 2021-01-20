##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import re

from odoo.addons.queue_job.job import job, related_action

from odoo import api, models, fields, _
from odoo.tools import config
from werkzeug.utils import escape

_logger = logging.getLogger(__name__)

# Mapping from Website form fields to res.partner fields in Odoo
SPONSOR_MAPPING = {
    "city": "city",
    "first_name": "firstname",
    "last_name": "lastname",
    "zipcode": "zip",
    "Beruf": "function",
    "phone": "phone",
    "street": "street",
    "email": "email",
    "kirchgemeinde": "church_name",
}

test_mode = config.get("test_enable")


class Contracts(models.Model):
    _inherit = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    group_id = fields.Many2one(required=False, readonly=False)
    partner_id = fields.Many2one(required=False, readonly=False)
    web_info = fields.Html()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create_sponsorship(
            self,
            child_local_id,
            form_data,
            sponsor_lang,
            utm_source,
            utm_medium,
            utm_campaign,
    ):
        """
        Called by Wordpress to add a new sponsorship.
        :param form_data: all form values entered on the site
        {
            'city': 'Bienne',
            'first_name': 'Emanuel',
            'last_name': 'Cino',
            'language': [u'französich', 'englisch'],
            'zahlungsweise': 'dauerauftrag',
            'consumer_source_text': 'Times Magazine',
            'zipcode': '2503',
            'birthday': '10/04/1989',
            'Beruf': 'Agriculteur paysan',
            'phone': '078 936 45 95',
            'consumer_source': 'Anzeige in Zeitschrift',
            'street': 'Rue test 1',
            'kirchgemeinde': u'Mon église',
            'mithelfen': {
                'checkbox': 'on'
            },
            'salutation': 'Herr',
            'patenschaftplus': {
                'checkbox': 'on'
            },
            'email': 'ecino@compassion.ch',
            'childID': '15783',
            'land': 'Suisse'
        }
        :param child_local_id: local id of child
        :param sponsor_lang: language used in the website
        :param utm_source: identifier from the url tracking
        :param utm_medium: identifier from the url tracking
        :param utm_campaign: identifier from the url tracking
        :return: True if process is good.
        """
        _logger.info(
            "New sponsorship for child %s from Wordpress: %s",
            child_local_id,
            str(form_data),
        )
        partner = self.env["res.partner"]
        try:
            form_data["Child reference"] = child_local_id

            for field in [
                "city",
                "first_name",
                "last_name",
                "consumer_source_text",
                "zipcode",
                "Beruf",
                "phone",
                "street",
                "kirchgemeinde",
                "email",
                "land",
            ]:
                form_data[field] = escape(form_data.get(field))

            match_obj = self.env["res.partner.match.wp"]

            partner_infos = {"company_id": self.env.user.company_id.id}
            for wp_field, odoo_field in list(SPONSOR_MAPPING.items()):
                partner_infos[odoo_field] = form_data.get(wp_field)

            # Match lang + title + spoken langs + country
            partner_infos["lang"] = match_obj.match_lang(sponsor_lang)
            form_data["lang"] = partner_infos["lang"]
            partner_infos["title"] = match_obj.match_title(form_data["salutation"])
            if form_data.get("language"):
                partner_infos["spoken_lang_ids"] = match_obj.match_spoken_langs(
                    form_data["language"]
                )
            partner_infos["country_id"] = match_obj.match_country(
                form_data["land"], partner_infos["lang"]
            ).id

            # Try to find a res.city.zip location for given data
            res_city_zip_obj = self.env["res.city.zip"]
            partner_location = res_city_zip_obj.search([
                ("name", '=', partner_infos.get("zip", None)),
                ("city_id.name", 'ilike', partner_infos.get("city"))
            ], limit=1)
            if not partner_location:
                partner_location = res_city_zip_obj.search([
                    ("name", '=', partner_infos.get('zip', None))
                ], limit=1)
            if len(partner_location) == 1:
                partner_infos.update({
                    "zip": partner_location.name,
                    "zip_id": partner_location.id,
                    "city": partner_location.city_id.name,
                    "city_id": partner_location.city_id.id,
                    "state": partner_location.city_id.state_id.name,
                    "state_id": partner_location.city_id.state_id.id,
                })
            else:
                # Remove bad address data
                partner_infos.pop("zip", False)
                partner_infos.pop("city", False)

            # Format birthday
            birthday = form_data.get("birthday", "")
            if birthday:
                d = birthday.split("/")  # 'dd/mm/YYYY' => ['dd', 'mm', 'YYYY']
                partner_infos["birthdate"] = "%s-%s-%s" % (d[2], d[1], d[0])

            # Search for existing partner
            partner = match_obj.match_partner_to_infos(partner_infos)
            if form_data.get("mithelfen", {}).get("checkbox") == "on":
                advocate_lang = partner.lang[:2]
                notify_user = self.env["ir.config_parameter"].get_param(
                    f"potential_advocate_{advocate_lang}")
                if notify_user:
                    partner.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary="Potential volunteer",
                        note="This person wants to ben involved with volunteering",
                        user_id=notify_user)

            # Check origin
            internet_id = self.env.ref("utm.utm_medium_website").id
            utms = self.env["utm.mixin"].get_utms(utm_source, utm_medium, utm_campaign)

            # Create sponsorship
            child = self.env["compassion.child"].search(
                [("local_id", "=", child_local_id)], limit=1
            )
            lines = self._get_sponsorship_standard_lines(utm_source == "wrpr")
            if not form_data.get("patenschaftplus"):
                lines = lines[:-1]
            sponsorship_type = "S"
            partner_id = partner.id
            if utm_source == "wrpr":
                # Special case Write&Pray sponsorship
                sponsorship_type = "SC"
                if form_data.get('writepray') == 'WRPR+DON':
                    contribution = float(form_data.get('writepray-contribution'))
                    for line in lines:
                        if line[2]['product_id'] == 2:
                            line[2].update({'amount': contribution,
                                            'subtotal': contribution,
                                            'quantity': 1})
                else:
                    partner_id = (
                            partner.search([("name", "=", "Donors of Compassion")],
                                           limit=1).id
                            or partner.id
                    )
            sponsorship_vals = {
                "partner_id": partner_id,
                "correspondent_id": partner.id,
                "child_id": child.id,
                "type": sponsorship_type,
                "contract_line_ids": lines,
                "next_invoice_date": fields.Date.today(),
                "source_id": utms["source"],
                "medium_id": utms.get("medium", internet_id),
                "campaign_id": utms["campaign"],
            }
        except:
            # We catch any exception to make sure we don't lose any
            # sponsorship made from the website
            self.env.clear()
            _logger.error("Error during wordpress sponsorship import", exc_info=True)
            sponsorship_vals = {
                "type": "S" if utm_source != "wrpr" else "SC",
                "child_id": self.env["compassion.child"]
                    .search([("local_id", "=", child_local_id)], limit=1)
                    .id,
            }
        finally:
            if not test_mode:
                return self.with_delay().create_sponsorship_job(
                    sponsorship_vals, form_data
                )
            else:
                return self.create_sponsorship_job(sponsorship_vals, form_data)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    @job(default_channel="root.child_sync_wp")
    @related_action(action="related_action_contract")
    def create_sponsorship_job(self, values, form_data):
        """
        Creates the wordpress sponsorship.
        :param values: dict for contract creation
        :param form_data: wordpress form data
        :return: <recurring.contract> record
        """
        sponsorship = self.env["recurring.contract"].create(values)
        list_keys = [
            "salutation",
            "first_name",
            "last_name",
            "birthday",
            "street",
            "zipcode",
            "city",
            "land",
            "email",
            "phone",
            "lang",
            "language",
            "kirchgemeinde",
            "Beruf",
            "zahlungsweise",
            "consumer_source",
            "consumer_source_text",
            "patenschaftplus",
            "mithelfen",
            "childID",
            "Child reference",
        ]
        web_info = ""
        for key in list_keys:
            web_info += ("<li>" + key + ": " + str(form_data.get(key, "")) + "</li>")
        sponsorship.web_info = web_info
        # Send confirmation to partner
        try:
            config = self.env.ref(
                "partner_communication_switzerland"
                ".config_onboarding_sponsorship_confirmation"
            )
            if not sponsorship.correspondent_id:
                sponsorship.correspondent_id = self.env["res.partner"].create({
                    "email": form_data.get("email"),
                    "name": form_data.get("first_name", "") + " " + form_data.get(
                        "last_name", ""),

                })
            sponsorship.send_communication(config)
            self.env.cr.commit()
        except:
            self.env.clear()
            _logger.error("No confirmation mail was sent to sponsor", exc_info=True)

        ambassador_match = re.match(
            r"^msk_(\d{1,8})", form_data.get("consumer_source_text", "")
        )
        event_match = re.match(r"^msk_(\d{1,8})", form_data.get("consumer_source", ""))
        # The sponsorships consumer_source fields were set automatically due
        # to a redirect from the sponsorship button on the muskathlon page.
        if ambassador_match and event_match:
            ambassador_id = int(ambassador_match.group(1))
            event_id = int(event_match.group(1))
            sponsorship.update(
                {
                    "user_id": ambassador_id,
                    "origin_id": self.env["recurring.contract.origin"]
                        .search([("event_id", "=", event_id)], limit=1)
                        .id,
                }
            )

        # Notify staff
        sponsor_lang = form_data["lang"][:2]
        staff_param = "sponsorship_" + sponsor_lang + "_id"
        staff = self.env["res.config.settings"].sudo().get_param(staff_param)
        notify_text = (
                          "A new sponsorship was made on the website. Please "
                          "verify all information and validate the sponsorship "
                          "on Odoo: <br/><br/><ul>"
                      ) + web_info

        title = _("New sponsorship from the website")
        if "writepray" in form_data:
            title = _("New Write&Pray sponsorship from the website")
        sponsorship.message_post(
            body=notify_text,
            subject=title,
            partner_ids=[staff],
            type="comment",
            subtype="mail.mt_comment",
            content_subtype="html",
        )

        sponsorship.correspondent_id.set_privacy_statement(origin="new_sponsorship")
        return sponsorship
