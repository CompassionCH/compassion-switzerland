##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import tempfile
import uuid
import base64

from odoo import api, registry, fields, models, _
from odoo.tools import mod10r
from odoo.tools.config import config

# fields that are synced if 'use_parent_address' is checked
ADDRESS_FIELDS = [
    "street",
    "street2",
    "street3",
    "zip",
    "city",
    "state_id",
    "country_id",
]

THANKYOU_MAPPING = {
    "none": "no",
    "auto_digital": "default",
    "auto_digital_only": "only_email",
    "digital": "default",
    "digital_only": "only_email",
    "physical": "paper",
}

logger = logging.getLogger(__name__)
MAGIC_INSTALLED = False

try:
    import magic
    MAGIC_INSTALLED = True
    import pyminizip
    import csv
    from smb.SMBConnection import SMBConnection
    from smb.smb_structs import OperationFailure
except ImportError:
    logger.warning("Please install python dependencies.", exc_info=True)


def get_file_type(data):
    ftype = ""
    if MAGIC_INSTALLED:
        ftype = magic.from_buffer(base64.b64decode(data), True)
    if "pdf" in ftype:
        return ".pdf"
    elif "tiff" in ftype:
        return ".tiff"
    elif "jpeg" in ftype:
        return ".jpg"
    elif "png" in ftype:
        return ".png"
    else:
        return ""


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """

    _inherit = "res.partner"

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################

    primary_segment_id = fields.Many2one(
        "res.partner.segment",
        string="Primary segmentation category",
        compute="_compute_segments",
        store=True
    )
    secondary_segment_id = fields.Many2one(
        "res.partner.segment",
        string="Secondary segmentation category",
        compute="_compute_segments",
        store=True
    )

    all_segments = fields.Many2many(
        "res.partner.segment.affinity",
        string="Affinity for each segment")

    lang = fields.Selection(default=False)
    total_invoiced = fields.Monetary(groups=False)
    # Track address changes
    street = fields.Char(track_visibility="onchange")
    city = fields.Char(track_visibility="onchange")
    street3 = fields.Char("Street3", size=128)
    invalid_mail = fields.Char("Invalid mail")
    church_unlinked = fields.Char(
        "Church (N/A)",
        help="Use this field if the church of the partner"
             " can not correctly be determined and linked.",
    )
    deathdate = fields.Date("Death date", track_visibility="onchange")
    nbmag = fields.Selection(
        [
            ("email", _("Email")),
            ("no_mag", _("No magazine")),
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
        ], string="Number of Magazines", required=True, default="one")
    tax_certificate = fields.Selection(
        [
            ("no", _("No receipt")),
            ("default", _("Default")),
            ("only_email", _("Only email")),
            ("paper", _("On paper")),
        ],
        required=True,
        default="default",
    )

    # Obsolete, rather use thankyou_preference kept for old template
    thankyou_letter = fields.Selection(
        [
            ("no", _("No receipt")),
            ("default", _("Default")),
            ("only_email", _("Only email")),
            ("paper", _("On paper")),
        ],
        "Thank you letter",
        compute="_compute_thankyou_letter",
    )
    calendar = fields.Boolean(
        help="Indicates if the partner wants to receive the Compassion " "calendar.",
        default=True,
    )
    christmas_card = fields.Boolean(
        help="Indicates if the partner wants to receive the " "christmas card.",
        default=True,
    )
    birthday_reminder = fields.Boolean(
        help="Indicates if the partner wants to receive a birthday "
             "reminder of his child.",
        default=True,
    )
    photo_delivery_preference = fields.Selection(
        selection="_get_delivery_preference",
        default="both",
        required=True,
        help="Delivery preference for Child photo",
    )

    partner_duplicate_ids = fields.Many2many(
        "res.partner",
        "res_partner_duplicates",
        "partner_id",
        "duplicate_id",
        readonly=True,
    )

    advocate_details_id = fields.Many2one(
        "advocate.details", "Advocate details", copy=False, readonly=False
    )
    engagement_ids = fields.Many2many(
        "advocate.engagement",
        related="advocate_details_id.engagement_ids",
        readonly=False,
    )
    other_contact_ids = fields.One2many(
        string="Linked Partners",
        domain=["|", ("active", "=", False), ("active", "=", True)],
        readonly=False,
    )

    email_copy = fields.Boolean(string="CC e-mails sent to main partner")
    type = fields.Selection(selection_add=[("email_alias", "Email alias")])

    uuid = fields.Char(copy=False, index=True)

    has_agreed_child_protection_charter = fields.Boolean(
        help="Indicates if the partner has agreed to the child protection" "charter.",
        default=False,
    )
    date_agreed_child_protection_charter = fields.Datetime(
        help="The date and time when the partner has agreed to the child"
             "protection charter."
    )
    criminal_record = fields.Binary(
        attachment=True,

    )
    criminal_record_name = fields.Char(
        compute="_compute_criminal_record_name"
    )
    criminal_record_date = fields.Date()

    # add track on fields from module base
    email = fields.Char(track_visibility="onchange")
    title = fields.Many2one(track_visibility="onchange", readonly=False)
    lang = fields.Selection(track_visibility="onchange")
    # module from partner_firstname
    firstname = fields.Char(track_visibility="onchange")
    lastname = fields.Char(track_visibility="onchange")
    # module mail
    opt_out = fields.Boolean(track_visibility="onchange")

    # Surveys
    survey_input_lines = fields.One2many(
        comodel_name="survey.user_input_line",
        inverse_name="partner_id",
        string="Surveys answers",
        readonly=False,
    )
    survey_inputs = fields.One2many(
        comodel_name="survey.user_input",
        inverse_name="partner_id",
        string="Surveys",
        readonly=False,
    )
    survey_input_count = fields.Integer(
        string="Survey number", compute="_compute_survey_input_count", store=True
    )
    city_id = fields.Many2one(related="zip_id.city_id", store=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def agree_to_child_protection_charter(self):
        return self.write(
            {
                "has_agreed_child_protection_charter": True,
                "date_agreed_child_protection_charter": fields.Datetime.now(),
            }
        )

    @api.multi
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

    @api.multi
    def update_number_sponsorships(self):
        """
        Update the sponsorship number for the related church as well.
        """
        return super().update_number_sponsorships()

    @api.depends("survey_inputs")
    def _compute_survey_input_count(self):
        for survey in self:
            survey.survey_input_count = len(survey.survey_inputs)

    def _compute_criminal_record_name(self):
        for partner in self:
            if partner.criminal_record:
                ftype = get_file_type(
                    partner.with_context(bin_size=False).criminal_record)
                partner.criminal_record_name = f"Criminal record {partner.name}{ftype}"

    @api.multi
    @api.depends("thankyou_preference")
    def _compute_thankyou_letter(self):
        """
        Keep the old way of preferences updated
        """
        for partner in self:
            partner.thankyou_letter = \
                THANKYOU_MAPPING[partner.thankyou_preference]

    @api.multi
    @api.depends("all_segments", "all_segments.affinity")
    def _compute_segments(self):
        for partner in self:
            affinity_for_segments = sorted([(s.affinity, s) for s in partner.all_segments])[::-1]

            if affinity_for_segments and len(affinity_for_segments) > 1:
                partner.primary_segment_id = affinity_for_segments[0][1].segment_id
                partner.secondary_segment_id = affinity_for_segments[1][1].segment_id

            elif affinity_for_segments and len(affinity_for_segments) > 0:
                partner.primary_segment_id = affinity_for_segments[0][1].segment_id
                partner.secondary_segment_id = None

            else:
                partner.primary_segment_id = None
                partner.secondary_segment_id = None

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """
        Lookup for duplicate partners and notify.
        """
        email = vals.get("email")
        if email:
            vals["email"] = email.strip()
        duplicate = self.search(
            [
                "|",
                "&",
                ("email", "=", vals.get("email")),
                ("email", "!=", False),
                "&",
                "&",
                ("firstname", "ilike", vals.get("firstname")),
                ("lastname", "ilike", vals.get("lastname")),
                ("zip", "=", vals.get("zip")),
            ]
        )
        duplicate_ids = [(4, itm.id) for itm in duplicate]
        vals.update({"partner_duplicate_ids": duplicate_ids})
        vals["ref"] = self.env["ir.sequence"].get("partner.ref")
        vals["uuid"] = uuid.uuid4()
        # Never subscribe someone to res.partner record
        partner = super(
            ResPartner, self.with_context(mail_create_nosubscribe=True)
        ).create(vals)
        partner.compute_geopoint()
        if partner.contact_type == "attached":
            partner.active = False

        return partner

    @api.multi
    def write(self, vals):
        email = vals.get("email")
        if email:
            vals["email"] = email.strip()
            # Push email to non-internal users
            user_ids = self.mapped("user_ids").filtered("share").ids
            self.env.cr.execute("""
                UPDATE res_users
                SET login=%s
                WHERE id=ANY(%s)
            """, [vals["email"], user_ids])
        if vals.get("criminal_record"):
            vals["criminal_record_date"] = fields.Date.today()
        res = super().write(vals)
        if {"country_id", "city", "zip"}.intersection(vals):
            self.geo_localize()
            self.compute_geopoint()
        return res

    @api.multi
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

    @api.model
    def _add_missing_default_values(self, values):
        """
        Fix bug changing the firstname and lastname because of automatic name
        computations. We remove the name value in the default values.
        """
        res = super()._add_missing_default_values(values)
        res.pop("name", False)
        return res

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=80):
        """Extends to use trigram search."""
        if args is None:
            args = []
        if name:
            # First find by reference
            res = self.search([("ref", "like", name)], limit=limit)
            if not res:
                res = self.search(
                    ["|", ("name", "%", name), ("name", "ilike", name)],
                    order="similarity(res_partner.name, '%s') DESC" % name,
                    limit=limit,
                )
            # Search by e-mail
            if not res:
                res = self.search([("email", "ilike", name)], limit=limit)
        else:
            res = self.search(args, limit=limit)
        return res.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """ Order search results based on similarity if name search is used."""
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
        return super().search(args, offset, limit, order, count)

    ##########################################################################
    #                             ONCHANGE METHODS                           #
    ##########################################################################
    @api.onchange("lastname", "firstname", "zip", "email")
    def _onchange_partner(self):
        if (
                (self.lastname and self.firstname and self.zip) or self.email
        ) and self.contact_type != "attached":
            partner_duplicates = self.search(
                [
                    ("id", "!=", self._origin.id),
                    "|",
                    "&",
                    ("email", "=", self.email),
                    ("email", "!=", False),
                    "&",
                    "&",
                    ("firstname", "ilike", self.firstname),
                    ("lastname", "ilike", self.lastname),
                    ("zip", "=", self.zip),
                ]
            )
            if partner_duplicates:
                self.partner_duplicate_ids = partner_duplicates
                # Commit the found duplicates
                with api.Environment.manage():
                    with registry(self.env.cr.dbname).cursor() as new_cr:
                        new_env = api.Environment(new_cr, self.env.uid, {})
                        self._origin.with_env(new_env).write(
                            {"partner_duplicate_ids": [(6, 0, partner_duplicates.ids)]}
                        )
                return {
                    "warning": {
                        "title": _("Possible existing partners found"),
                        "message": _(
                            "The partner you want to add may "
                            'already exist. Please use the "'
                            'Check duplicates" button to review it.'
                        ),
                    },
                }

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def compute_geopoint(self):
        """ Compute geopoints. """
        self.filtered(
            lambda p: not p.partner_latitude or not p.partner_longitude
        ).geo_localize()
        for partner in self.filtered(
                lambda p: p.partner_latitude and p.partner_longitude
        ):
            geo_point = fields.GeoPoint.from_latlon(
                self.env.cr, partner.partner_latitude, partner.partner_longitude
            )
            vals = {"geo_point": geo_point.wkt}
            partner.write(vals)
            partner.advocate_details_id.write(vals)
        return True

    @api.multi
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

    def action_view_partner_invoices(self):
        action = super().action_view_partner_invoices()
        action["domain"].clear()
        action["domain"].append(("type", "in", ["out_invoice", "out_refund"]))
        action["context"] = {"search_default_partner_id": self.id}
        return action

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def onchange_type(self, is_company):
        """ Put title 'Friends of Compassion for companies. """
        res = super().onchange_type(is_company)
        if is_company:
            res["value"]["title"] = self.env.ref(
                "partner_compassion.res_partner_title_friends"
            ).id
        return res

    @api.model
    def get_lang_from_phone_number(self, phone):
        record = self.env["phone.common"].get_record_from_phone_number(phone)
        if record:
            partner = self.browse(record[1])
        return record and partner.lang

    @api.multi
    def forget_me(self):
        # Store information in CSV, inside encrypted zip file.
        self._secure_save_data()

        super().forget_me()
        # Delete other objects and custom CH fields
        self.write(
            {
                "church_id": False,
                "church_unlinked": False,
                "street3": False,
                "firstname": False,
                "deathdate": False,
                "geo_point": False,
                "partner_latitude": False,
                "partner_longitude": False,
                "birthdate_date": False,
                "invalid_mail": False,
            }
        )
        self._cr.execute("update res_partner set ref=NULL, global_id=NULL where id=%s",
                         [self.id])
        self.advocate_details_id.sudo().unlink()
        self.survey_inputs.sudo().unlink()
        self.env["mail.tracking.email"].sudo().search([
            ("partner_id", "=", self.id)]).unlink()
        self.env["auditlog.log"].sudo().search(
            [("model_id.model", "=", "res.partner"), ("res_id", "=", self.id)]
        ).unlink()
        self.env["partner.communication.job"].sudo().search(
            [("partner_id", "=", self.id)]
        ).unlink()
        self.message_ids.sudo().unlink()
        return True

    @api.multi
    def open_duplicates(self):
        if not (self.partner_duplicate_ids - self):
            # No more duplicates, we just remove them
            self.partner_duplicate_ids = False
            return True
        partner_wizard = self.env["res.partner.check.double"].create(
            {"partner_id": self.id, }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner.check.double",
            "res_id": partner_wizard.id,
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
        }

    @api.multi
    def search_bank_address(self):
        return {
            'name': _('Search address in banks data'),
            'type': 'ir.actions.act_window',
            'res_model': 'search.bank.address.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'partner_compassion.search_bank_address_wizard_form').id,
            'target': 'new'
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS)

    def _secure_save_data(self):
        """
        Stores partner name and address in a CSV file on NAS,
        inside a password-protected ZIP file.
        :return: None
        """
        smb_conn = self._get_smb_connection()
        if smb_conn and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port):
            config_obj = self.env["ir.config_parameter"].sudo()
            share_nas = config_obj.get_param("partner_compassion.share_on_nas")
            store_path = config_obj.get_param("partner_compassion.store_path")
            src_zip_file = tempfile.NamedTemporaryFile()
            attrs = smb_conn.retrieveFile(share_nas, store_path, src_zip_file)
            file_size = attrs[1]
            if file_size:
                src_zip_file.flush()
                zip_dir = tempfile.mkdtemp()
                pyminizip.uncompress(src_zip_file.name, SmbConfig.file_pw, zip_dir, 0)
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
                    csv_path, "", dst_zip_file.name, SmbConfig.file_pw, 5
                )
                try:
                    smb_conn.storeFile(share_nas, store_path, dst_zip_file)
                except OperationFailure:
                    logger.error(
                        "Couldn't store secure partner data on NAS. "
                        "Please do it manually by replicating the following "
                        "file: " + dst_zip_file.name
                    )

    def _get_smb_connection(self):
        """" Retrieve configuration SMB """
        if not (
                SmbConfig.smb_user
                and SmbConfig.smb_pass
                and SmbConfig.smb_ip
                and SmbConfig.smb_port
        ):
            return False
        else:
            return SMBConnection(SmbConfig.smb_user, SmbConfig.smb_pass, "odoo", "nas")

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

    @api.model
    def _notify_prepare_email_values(self, message):
        """
        Always put reply_to value in mail notifications.
        :param message: the message record
        :return: mail values
        """
        mail_values = super()._notify_prepare_email_values(message)

        # Find reply-to in mail template.
        base_template = None
        if message.model and self._context.get("custom_layout", False):
            base_template = self.env.ref(
                self._context["custom_layout"], raise_if_not_found=False
            )
        if not base_template:
            base_template = self.env.ref(
                "mail.mail_template_data_notification_email_default"
            )

        if base_template.reply_to:
            mail_values["reply_to"] = base_template.reply_to

        return mail_values


class SmbConfig:
    """" Little class who contains SMB configuration """

    smb_user = config.get("smb_user")
    smb_pass = config.get("smb_pwd")
    smb_ip = config.get("smb_ip")
    smb_port = int(config.get("smb_port", 0))
    file_pw = config.get("partner_data_password")
