##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
import re
import tempfile

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import mod10r
from odoo.tools.config import config

logger = logging.getLogger(__name__)
regex_order = re.compile(r"^similarity\((.*),.*\)(\s+(desc|asc))?$", re.I)

try:
    import csv

    import phonenumbers
    import pyminizip
    import pysftp
    from pysftp import RSAKey
except ImportError:
    logger.warning("Please install python dependencies.", exc_info=True)


class ResPartner(models.Model):
    """This class upgrade the partners to match Compassion needs.
    It also synchronizes all changes with the MySQL server of GP.
    """

    _inherit = "res.partner"

    MAJORITY_AGE = 18
    YOUNG_AGE = 25

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    lang = fields.Selection(default=False, tracking=True)
    total_invoiced = fields.Monetary(groups=False)
    # Track address changes
    street = fields.Char(tracking=True)
    city = fields.Char(tracking=True)
    invalid_mail = fields.Char("Invalid mail")
    church_unlinked = fields.Char(
        "Church (N/A)",
        help="Use this field if the church of the partner"
        " can not correctly be determined and linked.",
    )
    deathdate = fields.Date("Death date", tracking=True)
    nbmag = fields.Selection(
        [
            ("email", "Email"),
            ("no_mag", "No magazine"),
            ("one", "1"),
            ("two", "2"),
            ("three", "3"),
            ("four", "4"),
            ("five", "5"),
            ("six", "6"),
            ("seven", "7"),
            ("eight", "8"),
            ("nine", "9"),
            ("ten", "10"),
            ("fifteen", "15"),
            ("twenty", "20"),
            ("twenty_five", "25"),
            ("fifty", "50"),
        ],
        string="Number of Magazines",
        required=True,
        default="one",
    )
    tax_certificate = fields.Selection(
        [
            ("no", "No receipt"),
            ("default", "Default"),
            ("only_email", "Only email"),
            ("paper", "On paper"),
        ],
        required=True,
        default="default",
    )
    birthday_reminder = fields.Boolean(
        help="Indicates if the partner wants to receive a birthday "
        "reminder of his child.",
        default=True,
    )
    sponsorship_anniversary_card = fields.Boolean(
        help="Indicates the partner wants to receive a card when we celebrate "
        "his or her sponsorship anniversary.",
        default=True,
    )

    partner_duplicate_ids = fields.Many2many(
        "res.partner",
        "res_partner_duplicates",
        "partner_id",
        "duplicate_id",
    )

    advocate_details_id = fields.Many2one(
        "advocate.details", "Advocate details", copy=False, readonly=False
    )
    interested_for_volunteering = fields.Boolean()
    is_volunteer = fields.Boolean(compute="_compute_is_volunteer")
    engagement_ids = fields.Many2many(
        "advocate.engagement",
        compute="_compute_engagement_ids",
        inverse="_inverse_engagement_ids",
        readonly=False,
    )

    email_copy = fields.Boolean(string="CC e-mails sent to main partner")
    type = fields.Selection(
        selection_add=[("email_alias", "Email alias")],
        ondelete={"email_alias": "set default"},
    )

    # add track on fields from module base
    email = fields.Char(tracking=True)
    title = fields.Many2one(tracking=True, readonly=False)
    # module from partner_firstname
    firstname = fields.Char(tracking=True)
    lastname = fields.Char(tracking=True)
    # module mail
    opt_out = fields.Boolean(tracking=True)
    city_id = fields.Many2one(related="zip_id.city_id", store=True)
    write_and_pray = fields.Boolean(
        string="Write & Pray",
        help="Have at least one sponsorship for the W&P program",
        compute="_compute_write_and_pray",
    )
    address_name = fields.Char(
        compute="_compute_address_name",
        inverse=lambda p: True,
        store=True,
        help="Name used for postal sending",
    )

    parent_consent = fields.Selection(
        [
            ("not_submitted", "Not submitted yet."),
            ("waiting", "Waiting Compassion approval"),
            ("approved", "Approved"),
            ("refused", "Refused"),
        ],
        string="Parent consents",
        default="not_submitted",
        required=True,
        tracking=True,
    )

    can_manage_paid_sponsorships = fields.Boolean(
        compute="_compute_can_manage_paid_sponsorships",
        help="Sponsor has 18 years old or has parents consent "
        "for paying sponsorship",
    )
    has_majority = fields.Boolean(
        compute="_compute_has_majority",
        help="Tells whether the partner has less than 18 years.",
    )
    is_young = fields.Boolean(
        compute="_compute_is_young",
        help="Tells whether the partner has less than 25 years.",
    )
    signup_url = fields.Char(
        compute="_compute_signup_url",
        help="Kept for our mail templates: Odoo 18 replaced this field by the "
        "_get_signup_url() method. res.users inherits it through its "
        "delegation to res.partner.",
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    # the token payload holds the linked users, so creating one changes the url
    @api.depends("signup_type", "user_ids")
    def _compute_signup_url(self):
        for partner in self:
            partner.signup_url = partner._get_signup_url()

    def _compute_has_majority(self):
        for record in self:
            record.has_majority = record.age >= self.MAJORITY_AGE

    def _compute_is_young(self):
        for partner in self:
            partner.is_young = partner.age < self.YOUNG_AGE

    def _compute_can_manage_paid_sponsorships(self):
        for record in self:
            record.can_manage_paid_sponsorships = (
                record.has_majority or record.parent_consent in ["approved"]
            )

    @api.depends("advocate_details_id")
    def _compute_is_volunteer(self):
        for partner in self:
            partner.is_volunteer = (
                partner.advocate_details_id.engagement_ids
                and partner.advocate_details_id.state != "inactive"
            )

    def get_unreconciled_amount(self):
        """Returns the amount of unreconciled credits in Account 1050"""
        self.ensure_one()
        mv_line_obj = self.env["account.move.line"]
        move_line_ids = mv_line_obj.search(
            [
                ("partner_id", "=", self.id),
                ("account_id.code", "=", "1050"),
                ("credit", ">", "0"),
                ("full_reconcile_id", "=", False),
            ]
        )
        res = 0
        for move_line in move_line_ids:
            res += move_line.credit
        return res

    def _compute_write_and_pray(self):
        for partner in self:
            partner.write_and_pray = "SWP" in partner.mapped("sponsorship_ids.type")

    @api.depends("name", "title", "lang")
    def _compute_address_name(self):
        for partner in self:
            if partner.title and not partner.is_company:
                partner.address_name = (partner.short_address or "").split("<br/>")[0]
            else:
                partner.address_name = partner.name

    def _compute_engagement_ids(self):
        for partner in self:
            partner.engagement_ids = partner.advocate_details_id.engagement_ids

    def _inverse_engagement_ids(self):
        for partner in self:
            if not partner.advocate_details_id and partner.engagement_ids:
                partner.advocate_details_id = self.env["advocate.details"].create(
                    {
                        "partner_id": partner.id,
                        "active_since": fields.Date.today(),
                        "advocacy_source": ", ".join(
                            partner.engagement_ids.mapped("name")
                        ),
                    }
                )
            partner.advocate_details_id.engagement_ids = partner.engagement_ids
            if not partner.engagement_ids and partner.advocate_details_id:
                partner.advocate_details_id.set_inactive()
            if (
                partner.engagement_ids
                and partner.advocate_details_id.state == "inactive"
            ):
                partner.advocate_details_id.set_active()

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_duplicates(vals)
            vals["ref"] = self.env["ir.sequence"].get("partner.ref")
            self.check_phone_and_mobile(vals)

        # Never subscribe someone to res.partner record
        partner = super(
            ResPartner, self.with_context(mail_create_nosubscribe=True)
        ).create(vals_list)
        return partner

    def write(self, vals):
        # Avoid cascading the name from the user
        if "name" in vals and self.env.context.get("write_from_user"):
            del vals["name"]
            if not vals:
                return True
        if vals.get("interested_for_volunteering"):
            # Notify volunteer staff, once, of a partner who just said yes.
            #
            # Only the ones the flag is new for: it is written by more than
            # the form that asks for it (the Wordpress connector, an import,
            # a staff member re-saving the record), and re-announcing an
            # advocate we already know about would put a second todo on
            # someone's list for nothing.
            #
            # This ran on write() only and never on create(), which for
            # years meant it never ran at all for a web signup - everything
            # about the partner arrived in one create(). The fast checkout
            # creates the partner before it knows who they are and writes
            # the rest afterwards, so this is now a live notification.
            newly_interested = self.filtered(
                lambda p: not p.advocate_details_id
                and not p.interested_for_volunteering
            )
            settings = self.env["res.config.settings"]
            for partner in newly_interested:
                # lang is deliberately left empty on this model, so a partner
                # created by a web flow has none of their own - the language
                # they are being served in is the next best answer.
                advocate_lang = (partner.lang or self.env.lang or "")[:2]
                param = f"potential_advocate_{advocate_lang}"
                if param not in settings._fields:
                    # There is a recipient setting for French, German and
                    # Italian and for nothing else, and asking for a setting
                    # that does not exist raises rather than answering
                    # (res.config.settings._get_classified_fields). So an
                    # English-speaking sponsor - or one who has told us no
                    # language at all - used to take the whole write down
                    # with them. Logged rather than silently dropped: it
                    # means a volunteer offer nobody was told about.
                    logger.warning(
                        "No potential-volunteer recipient is configured for"
                        " language %r; partner %s offered to volunteer and"
                        " no one was notified.",
                        advocate_lang,
                        partner.id,
                    )
                    continue
                notify_user = settings.get_param(param)
                if notify_user:
                    partner.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary="Potential volunteer",
                        note="This person wants to be involved with " "volunteering",
                        user_id=notify_user,
                    )

        self.check_phone_and_mobile(vals)
        self._unlink_mailing_contacts_if_needed(vals)
        self._check_duplicates(vals)

        res = super().write(vals)
        if {"country_id", "city", "zip"}.intersection(vals):
            self.geo_localize()
        return res

    @api.returns(None, lambda value: value[0])
    def copy_data(self, default=None):
        """
        Fix bug changing the firstname and lastname because of automatic name
        computations. We remove the name value in the copy fields.
        """
        res = super().copy_data(default)
        res[0].pop("name", False)
        return res

    def _contact_fields(self):
        """
        Fix bug changing the firstname and lastname because of automatic name
        computations. We remove the name value in the contact fields.
        """
        res = super()._contact_fields()
        res.remove("name")
        return res

    def _add_missing_default_values(self, values):
        """
        Fix bug changing the firstname and lastname because of automatic name
        computations. We remove the name value in the default values.
        """
        res = super()._add_missing_default_values(values)
        res.pop("name", False)
        return res

    def _inverse_name(self):
        """
        Fix bug changing the firstname and lastname because of automatic name
        computations. When the written name still matches the stored
        firstname/lastname combination, we keep them as they are instead of
        re-splitting the name. This prevents corrupting couple names like
        "John und Jane Smith" (firstname="John und Jane",
        lastname="Smith") into firstname="John", lastname="und Jane
        Smith" when the unchanged name is written back (e.g. by the
        website checkout during an online donation).
        """
        to_split = self.filtered(
            lambda p: (p.name or "")
            != (p._get_computed_name(p.lastname, p.firstname) or "")
        )
        if to_split:
            return super(ResPartner, to_split)._inverse_name()

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Extends to use trigram search."""
        if args is None:
            args = []
        if name:
            # First find by reference
            res = self.search([("ref", "like", name)], limit=limit)
            if not res:
                res = self.search(
                    ["|", ("name", "%", name), ("name", "ilike", name)],
                    order=f"similarity(name, '{name}') DESC",
                    limit=limit,
                )
            # Search by e-mail
            if not res:
                res = self.search([("email", "ilike", name)], limit=limit)
        else:
            res = self.search(args, limit=limit)
        return [(r.id, r.display_name) for r in res]

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Order search results based on similarity if name search is used."""
        fuzzy_search = False
        for arg in args:
            if arg[0] == "name" and arg[1] == "%":
                fuzzy_search = arg[2]
                break
        if fuzzy_search:
            order = self.env.cr.mogrify(
                "similarity(res_partner.name, %s) DESC", [fuzzy_search]
            )
        if order and isinstance(order, bytes):
            order = order.decode("utf-8")
        return super().search(args, offset=offset, limit=limit, order=order)

    def _check_qorder(self, word):
        """Allow similarity order"""
        try:
            super()._check_qorder(word)
        except UserError:
            if not regex_order.match(word):
                raise
        return True

    def _check_duplicates(self, vals):
        """
        Generates a search domain to find duplicates for this partner based
        on various filters
        :param dict vals: a dictionary containing values to write
        """
        if "partner_duplicate_ids" in vals:
            return False

        base = [("id", "not in", self.ids)]
        candidates = []

        email = vals.get("email")
        if email:
            candidates.append(["&", ("email", "=", email), ("email", "!=", False)])

        firstname = vals.get("firstname")
        lastname = vals.get("lastname")
        zip_code = vals.get("zip")
        street = vals.get("street")

        if firstname and lastname and zip_code:
            candidates.append(
                [
                    ("firstname", "ilike", firstname),
                    ("lastname", "ilike", lastname),
                    ("zip", "=", zip_code),
                ]
            )

        if lastname and street and zip_code:
            candidates.append(
                [
                    ("lastname", "ilike", lastname),
                    ("zip", "=", zip_code),
                    ("street", "ilike", street),
                ]
            )

        if not candidates:
            vals["partner_duplicate_ids"] = [Command.clear()]
            return self.browse()

        domain = expression.AND([base, expression.OR(candidates)])

        duplicates = self.search(domain)
        vals["partner_duplicate_ids"] = [Command.set(duplicates.ids)]
        return duplicates

    ##########################################################################
    #                             ONCHANGE METHODS                           #
    ##########################################################################
    @api.onchange("type")
    def _onchange_type(self):
        # Less likely that a contact has the same name as a company
        if self.parent_id and self.type == "contact":
            self.name = False
            self.firstname = False
            self.lastname = False
            self.title = False
        elif self.parent_id:
            self.name = self.parent_id.name
            self.title = self.parent_id.title
            self.firstname = self.parent_id.firstname
            self.lastname = self.parent_id.lastname

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def generate_bvr_reference(self, product):
        """
        Generates a bvr reference for a donation to the fund given by
        the product.
        :param product: fund product with a fund_id
        :return: bvr reference for the partner
        """
        self.ensure_one()
        if isinstance(product, int):
            product = self.env["product.product"].browse(product)
        ref = self.ref
        bvr_reference = "0" * (9 + (7 - len(ref))) + ref
        bvr_reference += "0" * 5
        bvr_reference += "6"  # Fund donation
        bvr_reference += "0" * (4 - len(str(product.fund_id))) + str(product.fund_id)
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

    def check_phone_and_mobile(self, vals):
        # Destination codes are the first two digits of a number
        all_swiss_phone_destination_codes = [
            21,
            22,
            24,
            26,
            27,
            31,
            32,
            33,
            34,
            41,
            43,
            44,
            51,
            52,
            55,
            56,
            58,
            61,
            62,
            71,
        ]

        # Destination codes are the first two digits of a mobile phone number
        all_swiss_mobile_destination_codes = [74, 75, 76, 77, 78, 79]

        # Check if the partner country is Switzerland
        swiss_country = self.env.ref("base.ch")
        if (
            vals.get("country_id") == swiss_country.id
            or self.country_id == swiss_country
        ):
            phone = vals.get("phone")
            phone_moved_to_mobile = False
            mobile = vals.get("mobile")

            if phone:
                parsed_phone = phonenumbers.parse(phone, "CH")
                if not phonenumbers.is_valid_number(parsed_phone):
                    raise UserError(_("Phone number is not valid."))
                phone_national_destination_code = int(
                    str(parsed_phone.national_number)[:2]
                )
                if (
                    phone_national_destination_code
                    in all_swiss_mobile_destination_codes
                ):
                    vals["mobile"] = phone
                    phone_moved_to_mobile = True
                    vals["phone"] = False

            if mobile:
                parsed_mobile = phonenumbers.parse(mobile, "CH")
                if not phonenumbers.is_valid_number(parsed_mobile):
                    raise UserError(_("Mobile number is not valid."))
                mobile_national_destination_code = int(
                    str(parsed_mobile.national_number)[:2]
                )
                if (
                    mobile_national_destination_code
                    in all_swiss_phone_destination_codes
                ):
                    vals["phone"] = mobile
                    if not phone_moved_to_mobile:
                        vals["mobile"] = False

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################

    def ensure_company_title_consistency(self):
        for partner in self:
            if partner.is_company:
                partner.title = self.env.ref(
                    "partner_compassion.res_partner_title_friends"
                ).id

    @api.depends("is_company", "title")
    def _compute_company_type(self):
        res = super()._compute_company_type()
        self.ensure_company_title_consistency()
        return res

    def _write_company_type(self):
        res = super()._write_company_type()
        self.ensure_company_title_consistency()
        return res

    def get_lang_from_phone_number(self, phone):
        record = self.env["phone.common"].get_record_from_phone_number(phone)
        if record:
            partner = self.browse(record[1])
        return record and partner.lang

    def anonymize(self, vals=None):
        # Store information in CSV, inside encrypted zip file.
        self._secure_save_data()

        # Delete other objects and custom CH fields
        self.mapped("mass_mailing_contact_ids").unlink()
        self.write(
            {
                "church_id": False,
                "church_unlinked": False,
                "street3": False,
                "firstname": False,
                "deathdate": False,
                "partner_latitude": False,
                "partner_longitude": False,
                "birthdate_date": False,
                "invalid_mail": False,
                "zip_id": False,
            }
        )
        self._cr.execute(
            "update res_partner set ref=NULL, global_id=NULL where id=%s", [self.id]
        )
        self.advocate_details_id.sudo().unlink()
        self.survey_inputs.sudo().unlink()
        self.env["mail.tracking.email"].sudo().search(
            [("partner_id", "=", self.id)]
        ).unlink()
        self.env["auditlog.log"].sudo().search(
            [("model_id.model", "=", "res.partner"), ("res_id", "=", self.id)]
        ).unlink()
        self.env["partner.communication.job"].sudo().search(
            [("partner_id", "=", self.id)]
        ).unlink()
        return super().anonymize(vals)

    def open_duplicates(self):
        if not (self.partner_duplicate_ids - self):
            # No more duplicates, we just remove them
            self.partner_duplicate_ids = False
            return True
        partner_wizard = self.env["res.partner.check.double"].create(
            {
                "partner_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner.check.double",
            "res_id": partner_wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def search_bank_address(self):
        return {
            "name": _("Search address in banks data"),
            "type": "ir.actions.act_window",
            "res_model": "search.bank.address.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "partner_compassion.search_bank_address_wizard_form"
            ).id,
            "target": "new",
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    @api.constrains("church_id")
    def _check_church_id(self):
        for record in self:
            if record.is_church and record.church_id:
                raise models.ValidationError(_("Cannot both be and have a church"))

    def _secure_save_data(self):
        """
        Stores partner name and address in a CSV file on NAS,
        inside a password-protected ZIP file.
        :return: None
        """
        sftp = self._get_sftp_connection()
        if sftp:
            config_obj = self.env["ir.config_parameter"].sudo()
            store_path = config_obj.get_param("partner_compassion.store_path")
            src_zip_file = tempfile.NamedTemporaryFile()
            file_size = sftp.getfo(store_path, src_zip_file)
            if file_size:
                src_zip_file.flush()
                zip_dir = tempfile.mkdtemp()
                pyminizip.uncompress(src_zip_file.name, SftpConfig.file_pw, zip_dir, 0)
                csv_path = zip_dir + "/partner_data.csv"
                with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(
                        [
                            str(self.id),
                            self.ref,
                            self.contact_address,
                            fields.Date.today(),
                        ]
                    )
                dst_zip_file = tempfile.NamedTemporaryFile()
                pyminizip.compress(
                    csv_path, "", dst_zip_file.name, SftpConfig.file_pw, 5
                )
                try:
                    sftp.putfo(dst_zip_file, store_path)
                except Exception:
                    logger.error(
                        "Couldn't store secure partner data on NAS. "
                        "Please do it manually by replicating the following "
                        "file: " + dst_zip_file.name
                    )
                finally:
                    src_zip_file.close()
                    dst_zip_file.close()

    def _get_sftp_connection(self):
        """ " Retrieve configuration SMB"""
        if not (
            SftpConfig.username
            and SftpConfig.password
            and SftpConfig.host
            and SftpConfig.port
        ):
            return False
        else:
            cnopts = pysftp.CnOpts()

            try:
                key_data = SftpConfig.ssh_key
                key = RSAKey(data=base64.decodebytes(key_data.encode("utf-8")))
                cnopts.hostkeys.add(SftpConfig.host, "ssh-rsa", key)
            except Exception:
                cnopts.hostkeys = None
                logger.warning(
                    "No hostkeys defined in StfpConnection. "
                    "Connection will be unsecured. "
                    "Please configure parameter "
                    "sbc_switzerland.nas_ssh_key with ssh_key data.",
                    exc_info=True,
                )

            return pysftp.Connection(
                username=SftpConfig.username,
                password=SftpConfig.password,
                port=SftpConfig.port,
                host=SftpConfig.host,
                cnopts=cnopts,
            )

    def _get_active_sponsorships_domain(self):
        """
        Include sponsorships of church members
        :return: search domain for recurring.contract
        """
        domain = super()._get_active_sponsorships_domain()
        domain.insert(0, "|")
        domain.insert(3, ("partner_id", "in", self.mapped("member_ids").ids))
        domain.insert(4, "|")
        domain.insert(6, ("correspondent_id", "in", self.mapped("member_ids").ids))
        return domain

    def _unlink_mailing_contacts_if_needed(self, vals):
        # ACLs shouldn't produce data inconsistency
        sudo = self.sudo()
        if "email" in vals:
            old_contacts = sudo.mapped("mass_mailing_contact_ids")
            new_contacts = sudo.env["mailing.contact"].search(
                [("email", "=", vals["email"]), ("id", "not in", old_contacts.ids)]
            )
            if old_contacts and new_contacts:
                old_contacts.unlink()
                new_contacts.write({"email": vals["email"]})
        mm_vals = {}
        if "active" in vals and not vals["active"]:
            mm_vals["active"] = False
        if "opt_out" in vals:
            subscription_ids = sudo.mapped(
                "mass_mailing_contact_ids.subscription_ids"
            ).ids
            mm_vals["subscription_ids"] = [
                (1, sub_id, {"opt_out": vals["opt_out"]}) for sub_id in subscription_ids
            ]
        if mm_vals and self.mapped("mass_mailing_contact_ids"):
            sudo.mapped("mass_mailing_contact_ids").write(mm_vals)


class SftpConfig:
    """ " Little class who contains SMB configuration"""

    username = config.get("sftp_user")
    password = config.get("sftp_pwd")
    host = config.get("sftp_ip")
    port = int(config.get("sftp_port", 22))
    file_pw = config.get("partner_data_password")
    ssh_key = config.get("sftp_ssh_key")
