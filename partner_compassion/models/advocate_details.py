##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import random
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.osv.expression import AND, OR
from odoo.tools import file_open

_logger = logging.getLogger(__name__)

# Non-translation recipients, used as the random fallback pool when a
# birthday reminder can't otherwise resolve a recipient (e.g. unconfigured
# language). Kept as a tuple of config_parameter keys rather than hardcoded
# names so it stays correct if responsibilities are reassigned later.
ADVOCATE_BIRTHDAY_FALLBACK_PARAMS = (
    "partner_compassion.advocate_birthday_fr_id",
    "partner_compassion.advocate_birthday_de_id",
    "partner_compassion.advocate_birthday_it_id",
    "partner_compassion.advocate_birthday_en_id",
)
SPEAKER_TRANSLATOR_XMLID = "partner_compassion.engagement_speaker_translator"

try:
    from pandas.tseries.offsets import BDay
except ImportError:
    _logger.warning("Please install pandas for the Advocate CRON to work")


class AdvocateDetails(models.Model):
    _name = "advocate.details"
    _description = "Advocate Details"
    _rec_name = "partner_id"
    _inherit = "mail.thread"

    partner_id = fields.Many2one(
        "res.partner", "Partner", required=True, ondelete="cascade", readonly=False
    )
    quote = fields.Text(translate=False)
    thank_you_quote = fields.Html(
        compute="_compute_thank_you_quote",
        help="Used in thank you letters for donations linked to an event "
        "and to this partner.",
    )
    mail_copy_when_donation = fields.Boolean()
    number_surveys = fields.Integer(
        related="partner_id.survey_input_count", readonly=False
    )

    # Advocacy fields
    #################
    active_since = fields.Date()
    end_date = fields.Date()
    last_event = fields.Date(compute="_compute_events")
    state = fields.Selection(
        [
            ("new", "New advocate"),
            ("active", "Active"),
            ("on_break", "On break"),
            ("inactive", "Inactive"),
        ],
        default="new",
        required=True,
        tracking=True,
    )
    break_end = fields.Date()
    advocacy_source = fields.Text(
        help="Describe how this advocate has partnered with us."
    )
    has_car = fields.Selection([("yes", "Yes"), ("no", "No")], "Has a car")
    formation_ids = fields.Many2many(
        "calendar.event",
        string="Formation taken",
        compute="_compute_formation",
        inverse="_inverse_formation",
        groups="base.group_user",
        readonly=False,
    )
    engagement_ids = fields.Many2many(
        "advocate.engagement",
        "advocate_engagement_rel",
        "advocate_details_id",
        "engagement_id",
        "Engagement type",
        readonly=False,
    )
    engagement_name = fields.Char(related="engagement_ids.name")
    t_shirt_size = fields.Selection(
        [("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL"), ("XXL", "XXL")]
    )
    t_shirt_type = fields.Selection(
        [
            ("shirt", "Shirt"),
            ("bikeshirt", "Bikeshirt"),
        ]
    )
    event_ids = fields.Many2many(
        "crm.event.compassion",
        string="Events",
        compute="_compute_events",
        readonly=False,
    )
    event_type_formation = fields.Integer(compute="_compute_formation")
    number_events = fields.Integer(compute="_compute_events")

    # Partner related fields
    ########################
    birthdate = fields.Date(
        related="partner_id.birthdate_date", store=True, readonly=True
    )
    lang = fields.Selection(related="partner_id.lang", store=True, readonly=True)
    zip = fields.Char(related="partner_id.zip", store=True, readonly=True)
    city = fields.Char(related="partner_id.city", store=True, readonly=True)
    email = fields.Char(related="partner_id.email", store=True, readonly=True)
    partner_latitude = fields.Float(related="partner_id.partner_latitude")
    partner_longitude = fields.Float(related="partner_id.partner_longitude")

    _sql_constraints = [
        (
            "details_unique",
            "unique(partner_id)",
            "Only one details per ambassador is allowed!",
        )
    ]

    def _compute_thank_you_quote(self):
        html_file = file_open(
            "partner_compassion/static/src/html/thank_you_quote_template.html"
        )
        template_html = str(html_file.read())
        self.get_base_url()
        for details in self:
            firstname = details.partner_id.firstname
            lastname = details.partner_id.lastname
            html_vals = {
                "img_alt": details.display_name,
                "image_url": f"{details.get_base_url()}/web/partner_image"
                f"/{details.partner_id.id}/image_512/{firstname}.jpg",
                "text": details.quote.strip() or "",
                "attribution": _("Quote from %(firstname)s %(lastname)s").format(
                    {"firstname": firstname, "lastname": lastname}
                )
                if details.quote.strip()
                else "",
            }
            details.thank_you_quote = template_html.format(**html_vals)

    def _compute_events(self):
        for details in self:
            details.event_ids = self.env["crm.event.compassion"].search(
                [
                    ("staff_ids", "=", details.partner_id.id),
                    ("end_date", "<", fields.Datetime.now()),
                ]
            )
            details.number_events = len(details.event_ids)
            if details.event_ids:
                details.last_event = details.event_ids[:1].end_date.date()
            else:
                details.last_event = False

    def _compute_formation(self):
        formation_cated_id = self.env.ref("partner_compassion.event_type_formation").id
        for details in self:
            details.formation_ids = self.env["calendar.event"].search(
                [
                    ("partner_ids", "=", details.partner_id.id),
                    ("categ_ids", "=", formation_cated_id),
                ]
            )
            details.event_type_formation = formation_cated_id

    def _inverse_formation(self):
        # Allows to create formation event from ambassador details
        return True

    @api.model_create_multi
    def create(self, vals_list):
        advocates_to_return = self.browse()
        vals_to_create = []

        partner_ids = [vals["partner_id"] for vals in vals_list]
        existing_advocates = self.search([("partner_id", "in", partner_ids)])
        existing_partner_ids = existing_advocates.partner_id.ids
        advocates_to_return |= existing_advocates

        for vals in vals_list:
            if vals["partner_id"] not in existing_partner_ids:
                vals_to_create.append(vals)

        if vals_to_create:
            advocates_to_return |= super().create(vals_to_create)

        for advocate in advocates_to_return:
            advocate.partner_id.advocate_details_id = advocate

        return advocates_to_return

    def open_events(self):
        return {
            "name": _("Events"),
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "crm.event.compassion",
            "target": "current",
            "domain": [("id", "in", self.event_ids.ids)],
        }

    def open_surveys(self):
        return {
            "name": _("Surveys"),
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "survey.user_input",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def set_on_break(self):
        self.env.user.notify_info(
            _("Please don't forget to put a break end date"), sticky=True
        )
        return self.write({"state": "on_break"})

    def set_inactive(self):
        return self.write({"state": "inactive", "end_date": fields.Date.today()})

    def set_active(self):
        return self.write({"state": "active", "end_date": False, "break_end": False})

    def _translation_engagements(self):
        # "Translation" is shipped module data (stable xmlid). "Speaker
        # Translator" isn't (it was created directly in the database) but
        # has been given a stable xmlid by a migration
        # (see migrations/18.0.1.0.1) so both are referenced by id here,
        # never by matching a (translatable, environment-dependent) name.
        engagements = self.env.ref("partner_compassion.engagement_translation")
        speaker_translator = self.env.ref(
            SPEAKER_TRANSLATOR_XMLID, raise_if_not_found=False
        )
        if speaker_translator:
            engagements |= speaker_translator
        return engagements

    def _advocate_birthday_recipient_id(self, advocate, translation_engagements=None):
        """Resolve which res.partner should be notified of this advocate's
        upcoming birthday: the dedicated translation recipient for
        translation-engagement advocates, otherwise whoever is configured
        for the advocate's language. Falls back to a random pick among the
        general (non-translation) recipients rather than dropping the
        reminder when nothing is configured for the case at hand.

        :param translation_engagements: pass this in when calling in a loop
            (e.g. from advocate_cron) to avoid a repeated search per advocate.
        """
        if translation_engagements is None:
            translation_engagements = self._translation_engagements()
        icp = self.env["ir.config_parameter"].sudo()
        if advocate.engagement_ids & translation_engagements:
            param = "partner_compassion.advocate_birthday_translation_id"
        else:
            lang = (advocate.partner_id.lang or "")[:2]
            param = f"partner_compassion.advocate_birthday_{lang}_id"
        partner_id = int(icp.get_param(param, 0) or 0)
        if partner_id:
            return partner_id

        fallback_ids = {
            int(icp.get_param(p, 0) or 0) for p in ADVOCATE_BIRTHDAY_FALLBACK_PARAMS
        }
        fallback_ids.discard(0)
        return random.choice(list(fallback_ids)) if fallback_ids else False

    def advocate_cron(self):
        three_open_days = datetime.today() + BDay(3)
        target_dates = [three_open_days]
        # A birthday landing on Sat/Sun is never exactly "3 business days"
        # from any weekday, so it would otherwise never be reminded at
        # all. Bundle the weekend into Friday's run (the last business day
        # before it) instead.
        if three_open_days.weekday() == 4:  # Friday
            target_dates.append(three_open_days + timedelta(days=1))
            target_dates.append(three_open_days + timedelta(days=2))

        domain = AND(
            [
                [("state", "in", ["active", "on_break"])],
                OR(
                    [
                        [("birthdate", "like", d.strftime("-%m-%d"))]
                        for d in target_dates
                    ]
                ),
            ]
        )
        birthday_advocates = self.search(domain)
        translation_engagements = self._translation_engagements()
        for advocate in birthday_advocates:
            try:
                notify_partner_id = self._advocate_birthday_recipient_id(
                    advocate, translation_engagements
                )
                if not notify_partner_id:
                    _logger.warning(
                        "No recipient configured for advocate birthday "
                        "reminder (advocate.details %s)",
                        advocate.id,
                    )
                    continue
                preferred_name = advocate.partner_id.preferred_name
                date = advocate.partner_id.get_date("birthdate_date", "d MMMM")
                display_name = advocate.display_name
                advocate.message_post(
                    body=_(
                        "This is a reminder that %(advocate_name)s will have "
                        "birthday on %(birthdate)s."
                    )
                    % {"advocate_name": preferred_name, "birthdate": date},
                    subject=_("[%s] Advocate birthday reminder") % display_name,
                    partner_ids=[notify_partner_id],
                    subtype_xmlid="mail.mt_comment",
                )
            except Exception:
                _logger.exception(
                    "Failed to send birthday reminder for advocate.details %s",
                    advocate.id,
                )
        break_advocates = self.search(
            [
                ("state", "=", "on_break"),
                ("break_end", "<", fields.Date.today()),
                ("break_end", "!=", False),
            ]
        )
        break_advocates.set_active()
