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
from random import randint

from markupsafe import escape

from odoo import _, api, fields, models
from odoo.tools import config, html2plaintext

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

CONTINENT_MAPPING = {
    # French
    "Asie": "Asia",
    "Afrique": "Africa",
    "Amérique Latine & Caraïbes": "LATAM",
    # German
    "Asien": "Asia",
    "Afrika": "Africa",
    "Lateinamerika & Karibik": "LATAM",
    # Italian
    "Asia": "Asia",
    "Africa": "Africa",
    "America Latina e Caraibi": "LATAM",
}

CONTINENT_COUNTRY_MAP = {
    "Africa": [
        "BF",  # Burkina Faso
        "ET",  # Ethiopia
        "GH",  # Ghana
        "KE",  # Kenya
        "RW",  # Rwanda
        "TG",  # Togo
        "TZ",  # Tanzania
        "UG",  # Uganda
    ],
    "Asia": [
        "BD",  # Bangladesh
        "ID",  # East Indonesia
        "IO",  # Indonesia
        "LK",  # Sri Lanka
        "PH",  # Philippines
        "TH",  # Thailand
    ],
    "LATAM": [
        "BO",  # Bolivia
        "BR",  # Brazil
        "CO",  # Colombia
        "DR",  # Dominican Republic
        "EC",  # Ecuador
        "ES",  # El Salvador
        "GU",  # Guatemala
        "HA",  # Haiti
        "HO",  # Honduras
        "ME",  # Mexico
        "NI",  # Nicaragua
        "PE",  # Peru
    ],
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
            partner_location = res_city_zip_obj.search(
                [
                    ("name", "=", partner_infos.get("zip", None)),
                    ("city_id.name", "ilike", partner_infos.get("city")),
                ],
                limit=1,
            )
            if not partner_location:
                partner_location = res_city_zip_obj.search(
                    [("name", "=", partner_infos.get("zip", None))], limit=1
                )
            if len(partner_location) == 1:
                partner_infos.update(
                    {
                        "zip": partner_location.name,
                        "zip_id": partner_location.id,
                        "city": partner_location.city_id.name,
                        "city_id": partner_location.city_id.id,
                        "state": partner_location.city_id.state_id.name,
                        "state_id": partner_location.city_id.state_id.id,
                    }
                )
            else:
                # Remove bad address data
                partner_infos.pop("zip", False)
                partner_infos.pop("city", False)

            # Format birthday
            birthday = form_data.get("birthday", "")
            if birthday:
                d = birthday.split("/")
                if len(d) == 3:
                    partner_infos["birthdate"] = f"{d[2]}-{d[1]}-{d[0]}"

            # Search for existing partner
            partner = match_obj.match_values_to_partner(partner_infos)
            if form_data.get("mithelfen", {}).get("checkbox") == "on":
                if (
                    not partner.advocate_details_id
                    and not partner.interested_for_volunteering
                ):
                    partner.interested_for_volunteering = True

            # Check origin
            internet = self.env.ref("utm.utm_medium_website")
            u_source = self.env["utm.source"].search([("name", "=", utm_source)])
            u_campaign = self.env["utm.campaign"].search([("name", "=", utm_campaign)])
            u_medium = (
                self.env["utm.medium"].search([("name", "=", utm_medium)]) or internet
            )

            # Create sponsorship
            child = self.env["compassion.child"].search(
                [("local_id", "=", child_local_id)], limit=1
            )
            lines = self._get_sponsorship_standard_lines(utm_source == "wrpr")
            if not form_data.get("patenschaftplus"):
                lines = lines[:-1]
            sponsorship_type = "S"
            # TODO to improve when switching to REST (with at least filter the company)
            pricelist_id = (
                self.env["product.pricelist"]
                .search(
                    [("currency_id", "=", self.env.user.company_id.currency_id.id)]
                )[:1]
                .id
            )
            partner_id = partner.id
            if utm_source == "wrpr":
                # Special case Write&Pray sponsorship
                sponsorship_type = "SC"
                if form_data.get("writepray") == "WRPR+DON":
                    contribution = float(form_data.get("writepray-contribution"))
                    for line in lines:
                        if line[2]["product_id"] == 2:
                            line[2].update(
                                {
                                    "amount": contribution,
                                    "subtotal": contribution,
                                    "quantity": 1,
                                }
                            )
                else:
                    partner_id = (
                        partner.search(
                            [("name", "=", "Donors of Compassion")], limit=1
                        ).id
                        or partner.id
                    )
            sponsorship_vals = {
                "partner_id": partner_id,
                "correspondent_id": partner.id,
                "child_id": child.id,
                "type": sponsorship_type,
                "pricelist_id": pricelist_id,
                "contract_line_ids": lines,
                "source_id": u_source.id,
                "medium_id": u_medium.id,
                "campaign_id": u_campaign.id,
            }
        except Exception:
            # We catch any exception to make sure we don't lose any
            # sponsorship made from the website
            self.env.clear()
            _logger.error("Error during wordpress sponsorship import", exc_info=True)
            child = self.env["compassion.child"].search(
                [("local_id", "=", child_local_id)], limit=1
            )
            pricelist_id = (
                self.env["product.pricelist"]
                .search(
                    [("currency_id", "=", self.env.user.company_id.currency_id.id)]
                )[:1]
                .id
            )
            sponsorship_vals = {
                "type": "S" if utm_source != "wrpr" else "SC",
                "pricelist_id": pricelist_id,
                "child_id": child.id,
            }
            self.env.clear()
            # Notify staff
            child.activity_schedule(
                "mail.mail_activity_data_warning",
                summary="[URGENT] Sponsorship from website failed",
                note="Please verify this new sponsorship made from the website with "
                f"following information: {form_data} lang: {sponsor_lang} "
                f"source: {utm_source} medium: {utm_medium} "
                f"campaign: {utm_campaign}",
                user_id=21,  # EMA
            )
        return self.with_delay(
            channel="root.accounting",
            priority=5,
            identity_key=f"{self._name}.create_wordpress_sponsorship.{child_local_id}",
        ).create_sponsorship_job(sponsorship_vals, form_data)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def create_sponsorship_job(self, values, form_data):
        """Creates the WordPress sponsorship.
        :param values: dict for contract creation
        :param form_data: WordPress form data
        :return: <recurring.contract> record
        """
        child = self.env["compassion.child"].browse(values["child_id"])
        child.remove_from_wordpress()

        try:
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
                web_info += "<li>" + key + ": " + str(form_data.get(key, "")) + "</li>"
            sponsorship.web_info = web_info
            ambassador_match = re.match(
                r"^msk_(\d{1,8})", form_data.get("consumer_source_text", "")
            )
            event_match = re.match(
                r"^msk_(\d{1,8})", form_data.get("consumer_source", "")
            )
            # The sponsorships consumer_source fields were set automatically due
            # to a redirect from the sponsorship button on the muskathlon page.
            if ambassador_match and event_match:
                ambassador_id = int(ambassador_match.group(1))
                event_id = int(event_match.group(1))
                sponsorship.update(
                    {
                        "ambassador_id": ambassador_id,
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
                subtype_xmlid="mail.mt_comment",
                content_subtype="html",
            )

            sponsorship.correspondent_id.legal_agreement_date = fields.Datetime.now()
            return sponsorship
        except BaseException as err:
            # Log the error and send a mail stating that it failed running
            _logger.error("Wordpress create sponsorship job failed", exc_info=True)
            child.activity_schedule(
                "mail.mail_activity_data_warning",
                summary="[URGENT] Wordpress create sponsorship job failed",
                note="Please verify this new sponsorship made from the website with "
                f"following information: {str(form_data)}, "
                f"and given following values: {str(values)}, "
                f"with following error: {str(err)}",
                user_id=21,  # EMA
            )

    def message_new(self, msg_dict, custom_values=None):
        """
        Called when an email creates a sponsorship, which is the case for CSP
        Sponsorships for instance.
        @param msg_dict: mail message values
        @param custom_values: alias custom values
        @return: created record
        """
        if custom_values is None:
            custom_values = {}
        sponsorship_type = custom_values.get("type")
        notify_partner_id = False
        if sponsorship_type in ("CSP", "M2M"):
            form_data = self._parse_wp_sponsorship_form(msg_dict.get("body", ""))
            partner = self.env["res.partner"].search(
                [("email", "=", form_data["email"])], limit=1
            )
            lang_code = False
            if form_data.get("language"):
                lang_code = (
                    self.env["res.lang"]
                    .search([("name", "ilike", form_data["language"])], limit=1)
                    .code
                )
            lang_code = (
                (lang_code and lang_code[:2])
                or (partner.lang and partner.lang[:2])
                or "de"
            )

            if sponsorship_type == "CSP":
                country_code = form_data["country"]
                if not country_code:
                    country_code = self._get_neediest_csp_country_code(
                        form_data["continent"]
                    )

                product = self.env["product.product"].search(
                    [("default_code", "=", f"csp_{country_code}")], limit=1
                )
                ref = f"CSP-{country_code}-{partner.ref or randint(1000, 9999)}"
            else:
                product = self.env["product.product"].search(
                    [
                        ("default_code", "like", "m2m"),
                        ("default_code", "like", lang_code),
                    ],
                    limit=1,
                )
                ref = f"M2M-{partner.ref or randint(1000, 9999)}"

            custom_values.update(
                {
                    "partner_id": partner.id,
                    "contract_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "amount": form_data["amount"] or product.list_price,
                                "quantity": 1,
                                "subtotal": form_data["amount"] or product.list_price,
                            },
                        )
                    ],
                    "reference": ref,
                }
            )
            msg_dict["subject"] = ref
            msg_date = msg_dict.get("date")
            if msg_date:
                custom_values["create_date"] = msg_date
            notify_partner_field = f"sponsorship_{lang_code}_id"
            notify_partner_id = self.env["res.config.settings"].get_param(
                notify_partner_field
            )
        contract = super().message_new(msg_dict, custom_values)
        if notify_partner_id:
            contract.message_post(
                body=msg_dict["body"],
                subject=msg_dict["subject"],
                partner_ids=[notify_partner_id],
                message_type="email",
            )
        return contract

    def _parse_wp_sponsorship_form(self, data_string):
        """
        Parses a sponsorship application string and extracts specific information.

        Args:
            data_string: The string containing the sponsorship application data.

        Returns:
            dict: A dictionary with parsed form data.
        - 'country' (str): The applicant's country.
        - 'continent' (str): The applicant's continent (mapped via CONTINENT_MAPPING).
        - 'engagement_type' (str): The desired sponsorship level.
        - 'email' (str): The applicant's email.
        - 'sponsorship_length' (str): The sponsorship duration.
        """
        # Regex to capture the rest of the line after a specific label.
        country_regex = r"Country:\s*([^\n]*)"
        continent_regex = r"Continent:\s*([^\n]*)"
        engagement_regex = r"Engagement type:\s*([^\n]*)"
        email_regex = r"E-mail:\s*([^\n]*)"
        sponsorship_length_regex = r"Sponsorship length:\s*([^\n]*)"
        language_regex = r"Language\s*:\s*([^\n]*)"
        amount_regex = r"CHF\s*(\d+)"

        # Compile the regex patterns for efficiency
        country_pattern = re.compile(country_regex)
        continent_pattern = re.compile(continent_regex)
        engagement_pattern = re.compile(engagement_regex)
        email_pattern = re.compile(email_regex)
        sponsorship_length_pattern = re.compile(sponsorship_length_regex)
        language_pattern = re.compile(language_regex)
        amount_pattern = re.compile(amount_regex)

        # Extract information using regular expressions
        country_match = country_pattern.search(data_string)
        continent_match = continent_pattern.search(data_string)
        engagement_match = engagement_pattern.search(data_string)
        email_match = email_pattern.search(data_string)
        sponsorship_length_match = sponsorship_length_pattern.search(data_string)
        language_match = language_pattern.search(data_string)
        amount_match = amount_pattern.search(data_string)

        # Extract data from matches (handle cases where no match is found)
        country = country_match.group(1) if country_match else ""
        continent = continent_match.group(1) if continent_match else ""
        engagement_type = engagement_match.group(1) if engagement_match else ""
        email = email_match.group(1) if email_match else ""
        sponsorship_length = (
            sponsorship_length_match.group(1) if sponsorship_length_match else ""
        )
        language = language_match.group(1) if language_match else ""
        amount = amount_match.group(1) if amount_match else ""

        # Return a dictionary with the extracted information
        return {
            "country": html2plaintext(country),
            "continent": CONTINENT_MAPPING.get(html2plaintext(continent), "Africa"),
            "engagement_type": html2plaintext(engagement_type),
            "email": html2plaintext(email),
            "sponsorship_length": html2plaintext(sponsorship_length),
            "language": language,
            "amount": amount,
        }

    def _get_neediest_csp_country_code(self, continent=None):
        """
        Sort CSP products to find the country with the most needs.

        The neediest country is determined by two factors, in order of priority:
        1. The lowest percentage of used slots (prioritizing need).
        2. The highest number of absolute available slots (prioritizing capacity).

        Args:
            continent (str, optional): The continent ('Africa', 'Asia', 'LATAM')
                                       to search within. If None, searches globally.
        Returns:
            str: The two-letter country code (e.g., 'UG') of the neediest country
        """
        if continent:
            country_codes = CONTINENT_COUNTRY_MAP[continent]
        else:
            country_codes = [
                code
                for country_list in CONTINENT_COUNTRY_MAP.values()
                for code in country_list
            ]

        csp_sorted_by_needs = self.env["product.product"].search(
            [("default_code", "in", [f"csp_{code}" for code in country_codes])],
            order="slot_used ASC, survival_slot_number DESC",
            limit=1,
        )
        return csp_sorted_by_needs.default_code.split("_")[-1]
