# -*- coding: utf-8 -*-
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

from odoo import api, registry, fields, models, _
from odoo.tools import mod10r
from odoo.tools.config import config
from odoo.addons.base_geoengine.fields import GeoPoint
from odoo.addons.base_geoengine import fields as geo_fields

# fields that are synced if 'use_parent_address' is checked
ADDRESS_FIELDS = [
    'street', 'street2', 'street3', 'zip', 'city', 'state_id', 'country_id']

logger = logging.getLogger(__name__)

try:
    import pyminizip
    import csv
    from smb.SMBConnection import SMBConnection
    from smb.smb_structs import OperationFailure
except ImportError:
    logger.warning("Please install python dependencies.", exc_info=True)


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """
    _inherit = 'res.partner'

    def _get_receipt_types(self):
        """ Display values for the receipt selection fields. """
        return [
            ('no', _('No receipt')),
            ('default', _('Default')),
            ('only_email', _('Only email')),
            ('paper', _('On paper'))]

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    lang = fields.Selection(default=False)
    total_invoiced = fields.Monetary(groups=False)
    street3 = fields.Char("Street3", size=128)
    invalid_mail = fields.Char("Invalid mail")
    church_unlinked = fields.Char(
        "Church (N/A)",
        help="Use this field if the church of the partner"
             " can not correctly be determined and linked.")
    deathdate = fields.Date('Death date', track_visibility='onchange')
    nbmag = fields.Integer('Number of Magazines', size=2,
                           required=True, default=1)
    tax_certificate = fields.Selection(
        _get_receipt_types, required=True, default='default')
    thankyou_letter = fields.Selection(
        _get_receipt_types, 'Thank you letter',
        required=True, default='default')
    calendar = fields.Boolean(
        help="Indicates if the partner wants to receive the Compassion "
             "calendar.", default=True)
    christmas_card = fields.Boolean(
        help="Indicates if the partner wants to receive the "
             "christmas card.", default=True)
    birthday_reminder = fields.Boolean(
        help="Indicates if the partner wants to receive a birthday "
             "reminder of his child.", default=True)
    photo_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='both',
        required=True,
        help='Delivery preference for Child photo')

    partner_duplicate_ids = fields.Many2many(
        'res.partner', 'res_partner_duplicates', 'partner_id',
        'duplicate_id', readonly=True)

    advocate_details_id = fields.Many2one(
        'advocate.details', 'Advocate details', copy=False)
    engagement_ids = fields.Many2many(
        'advocate.engagement', related='advocate_details_id.engagement_ids'
    )
    other_contact_ids = fields.One2many(string='Linked Partners',
                                        domain=['|', ('active', '=', False),
                                                ('active', '=', True)])
    state = fields.Selection([
        ('pending', 'Waiting for validation'),
        ('active', 'Active')
    ], default='active', track_visibility='onchange')

    email_copy = fields.Boolean(string='CC e-mails sent to main partner')
    type = fields.Selection(selection_add=[
        ('email_alias', 'Email alias')
    ])

    uuid = fields.Char(default=lambda self: self._get_uuid(), copy=False,
                       index=True)

    has_agreed_child_protection_charter = fields.Boolean(
        help="Indicates if the partner has agreed to the child protection"
             "charter.", default=False)
    date_agreed_child_protection_charter = fields.Datetime(
        help="The date and time when the partner has agreed to the child"
             "protection charter."
    )
    geo_point = geo_fields.GeoPoint(copy=False)

    # add track on fields from module base
    email = fields.Char(track_visibility='onchange')
    title = fields.Many2one(track_visibility='onchange')
    lang = fields.Selection(track_visibility='onchange')
    # module from partner_firstname
    firstname = fields.Char(track_visibility='onchange')
    lastname = fields.Char(track_visibility='onchange')
    # module mail
    opt_out = fields.Boolean(track_visibility='onchange')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_uuid(self):
        return str(uuid.uuid4())

    @api.multi
    def agree_to_child_protection_charter(self):
        return self.write({
            'has_agreed_child_protection_charter': True,
            'date_agreed_child_protection_charter': fields.Datetime.now()
        })

    @api.multi
    def validate_partner(self):
        return self.write({
            'state': 'active'
        })

    @api.multi
    def get_unreconciled_amount(self):
        """Returns the amount of unreconciled credits in Account 1050"""
        self.ensure_one()
        mv_line_obj = self.env['account.move.line']
        move_line_ids = mv_line_obj.search([
            ('partner_id', '=', self.id),
            ('account_id.code', '=', '1050'),
            ('credit', '>', '0'),
            ('full_reconcile_id', '=', False)])
        res = 0
        for move_line in move_line_ids:
            res += move_line.credit
        return res

    @api.multi
    def update_number_sponsorships(self):
        """
        Update the sponsorship number for the related church as well.
        """
        return super(
            ResPartner,
            self + self.mapped('church_id')).update_number_sponsorships()

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """
        Lookup for duplicate partners and notify.
        """
        email = vals.get('email')
        if email:
            vals['email'] = email.strip()
        duplicate = self.search(
            ['|',
             '&',
             ('email', '=', vals.get('email')),
             ('email', '!=', False),
             '&', '&',
             ('firstname', 'ilike', vals.get('firstname')),
             ('lastname', 'ilike', vals.get('lastname')),
             ('zip', '=', vals.get('zip'))
             ])
        duplicate_ids = [(4, itm.id) for itm in duplicate]
        vals.update({'partner_duplicate_ids': duplicate_ids})
        vals['ref'] = self.env['ir.sequence'].get('partner.ref')
        # Never subscribe someone to res.partner record
        partner = super(ResPartner, self.with_context(
            mail_create_nosubscribe=True)).create(vals)
        partner.compute_geopoint()
        if partner.contact_type == 'attached' and not vals.get('active'):
            partner.active = False

        return partner

    @api.multi
    def write(self, vals):
        email = vals.get('email')
        if email:
            vals['email'] = email.strip()
        res = super(ResPartner, self).write(vals)
        if set(('country_id', 'city', 'zip')).intersection(vals):
            self.geo_localize()
            self.compute_geopoint()
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        """Extends to use trigram search."""
        if args is None:
            args = []
        if name:
            # First find by reference
            res = self.search([('ref', 'like', name)], limit=limit)
            if not res:
                res = self.search(
                    ['|', ('name', '%', name), ('name', 'ilike', name)],
                    order=u"similarity(res_partner.name, '%s') DESC" % name,
                    limit=limit)
            # Search by e-mail
            if not res:
                res = self.search([('email', 'ilike', name)], limit=limit)
        else:
            res = self.search(args, limit=limit)
        return res.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """ Order search results based on similarity if name search is used."""
        fuzzy_search = False
        for arg in args:
            if arg[0] == 'name' and arg[1] == '%':
                fuzzy_search = arg[2]
                break
        if fuzzy_search:
            order = u"similarity(res_partner.name, '%s') DESC" % fuzzy_search
        return super(ResPartner, self).search(
            args, offset, limit, order, count)

    ##########################################################################
    #                             ONCHANGE METHODS                           #
    ##########################################################################
    @api.onchange('lastname', 'firstname', 'zip', 'email')
    def _onchange_partner(self):
        if ((self.lastname and self.firstname and self.zip) or self.email)\
                and self.contact_type != 'attached':
            partner_duplicates = self.search([
                ('id', '!=', self._origin.id),
                '|',
                '&',
                ('email', '=', self.email),
                ('email', '!=', False),
                '&', '&',
                ('firstname', 'ilike', self.firstname),
                ('lastname', 'ilike', self.lastname),
                ('zip', '=', self.zip)
            ])
            if partner_duplicates:
                self.partner_duplicate_ids = partner_duplicates
                # Commit the found duplicates
                with api.Environment.manage():
                    with registry(self.env.cr.dbname).cursor() as new_cr:
                        new_env = api.Environment(new_cr, self.env.uid, {})
                        self._origin.with_env(new_env).write({
                            'partner_duplicate_ids': [(6, 0,
                                                       partner_duplicates.ids)]
                        })
                return {
                    'warning': {
                        'title': _("Possible existing partners found"),
                        'message': _('The partner you want to add may '
                                     'already exist. Please use the "'
                                     'Check duplicates" button to review it.')
                    },
                }

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def compute_geopoint(self):
        """ Compute geopoints. """
        self.filtered(lambda p: not p.partner_latitude or not
                      p.partner_longitude).geo_localize()
        for partner in self.filtered(lambda p: p.partner_latitude and
                                     p.partner_longitude):
            geo_point = GeoPoint.from_latlon(
                self.env.cr,
                partner.partner_latitude,
                partner.partner_longitude)
            vals = {'geo_point': geo_point.wkt}
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
            product = self.env['product.product'].browse(product)
        ref = self.ref
        bvr_reference = '0' * (9 + (7 - len(ref))) + ref
        bvr_reference += '0' * 5
        bvr_reference += '6'    # Fund donation
        bvr_reference += '0' * (4 - len(str(product.fund_id))) + str(
            product.fund_id)
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def onchange_type(self, is_company):
        """ Put title 'Friends of Compassion for companies. """
        res = super(ResPartner, self).onchange_type(is_company)
        if is_company:
            res['value']['title'] = self.env.ref(
                'partner_compassion.res_partner_title_friends').id
        return res

    @api.model
    def get_lang_from_phone_number(self, phone):
        record = self.env['phone.common'].get_record_from_phone_number(phone)
        if record:
            partner = self.browse(record[1])
        return record and partner.lang

    @api.multi
    def forget_me(self):
        # Store information in CSV, inside encrypted zip file.
        self._secure_save_data()

        super(ResPartner, self).forget_me()
        # Delete other objects and custom CH fields
        self.write({
            'church_id': False,
            'church_unlinked': False,
            'street3': False,
            'firstname': False,
            'deathdate': False,
            'geo_point': False,
            'partner_latitude': False,
            'partner_longitude': False
        })
        self.advocate_details_id.unlink()
        self.survey_inputs.unlink()
        self.env['mail.tracking.email'].search([
            ('partner_id', '=', self.id)]).unlink()
        self.env['auditlog.log'].search([
            ('model_id.model', '=', 'res.partner'),
            ('res_id', '=', self.id)
        ]).unlink()
        self.env['partner.communication.job'].search([
            ('partner_id', '=', self.id)
        ]).unlink()
        self.message_ids.unlink()
        return True

    @api.multi
    def open_duplicates(self):
        partner_wizard = self.env['res.partner.check.double'].create({
            'partner_id': self.id,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner.check.double",
            "res_id": partner_wizard.id,
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
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
            config_obj = self.env['ir.config_parameter']
            share_nas = config_obj.get_param('partner_compassion.share_on_nas')
            store_path = config_obj.get_param('partner_compassion.store_path')
            src_zip_file = tempfile.NamedTemporaryFile()
            attrs = smb_conn.retrieveFile(share_nas, store_path, src_zip_file)
            file_size = attrs[1]
            if file_size:
                src_zip_file.flush()
                zip_dir = tempfile.mkdtemp()
                pyminizip.uncompress(
                    src_zip_file.name, SmbConfig.file_pw, zip_dir, 0)
                csv_path = zip_dir + '/partner_data.csv'
                with open(csv_path, 'ab') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow([
                        str(self.id), self.ref, self.contact_address,
                        fields.Date.today()
                    ])
                dst_zip_file = tempfile.NamedTemporaryFile()
                pyminizip.compress(
                    csv_path, '', dst_zip_file.name, SmbConfig.file_pw, 5)
                try:
                    smb_conn.storeFile(share_nas, store_path, dst_zip_file)
                except OperationFailure:
                    logger.error(
                        "Couldn't store secure partner data on NAS. "
                        "Please do it manually by replicating the following "
                        "file: " + dst_zip_file.name)

    def _get_smb_connection(self):
        """" Retrieve configuration SMB """
        if not (SmbConfig.smb_user and SmbConfig.smb_pass and
                SmbConfig.smb_ip and SmbConfig.smb_port):
            return False
        else:
            return SMBConnection(
                SmbConfig.smb_user, SmbConfig.smb_pass, 'odoo', 'nas')

    def _get_active_sponsorships_domain(self):
        """
        Include sponsorships of church members
        :return: search domain for recurring.contract
        """
        domain = super(ResPartner, self)._get_active_sponsorships_domain()
        domain.insert(0, '|')
        domain.insert(3, ('partner_id', 'in', self.mapped('member_ids').ids))
        domain.insert(4, '|')
        domain.insert(6, ('correspondent_id', 'in', self.mapped(
            'member_ids').ids))
        return domain

    @api.model
    def _notify_prepare_email_values(self, message):
        """
        Always put reply_to value in mail notifications.
        :param message: the message record
        :return: mail values
        """
        mail_values = super(ResPartner,
                            self)._notify_prepare_email_values(message)

        # Find reply-to in mail template.
        base_template = None
        if message.model and self._context.get('custom_layout', False):
            base_template = self.env.ref(self._context['custom_layout'],
                                         raise_if_not_found=False)
        if not base_template:
            base_template = self.env.ref(
                'mail.mail_template_data_notification_email_default')

        if base_template.reply_to:
            mail_values['reply_to'] = base_template.reply_to

        return mail_values


class SmbConfig():
    """" Little class who contains SMB configuration """
    smb_user = config.get('smb_user')
    smb_pass = config.get('smb_pwd')
    smb_ip = config.get('smb_ip')
    smb_port = int(config.get('smb_port', 0))
    file_pw = config.get('partner_data_password')
