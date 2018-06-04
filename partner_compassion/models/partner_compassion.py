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
from odoo.tools import mod10r

from odoo import api, registry, fields, models, _

from odoo.addons.base_geoengine.fields import GeoPoint

# fields that are synced if 'use_parent_address' is checked
ADDRESS_FIELDS = [
    'street', 'street2', 'street3', 'zip', 'city', 'state_id', 'country_id']


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
            ('paper', _('On paper'))]

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    lang = fields.Selection(default=False)
    total_invoiced = fields.Monetary(groups=False)
    street3 = fields.Char("Street3", size=128)
    invalid_mail = fields.Char("Invalid mail")
    member_ids = fields.One2many(
        'res.partner', 'church_id', 'Members',
        domain=[('active', '=', True)])
    is_church = fields.Boolean(
        string="Is a Church", compute='_compute_is_church', store=True)
    church_id = fields.Many2one(
        'res.partner', 'Church', domain=[('is_church', '=', True)])
    church_unlinked = fields.Char(
        "Church (N/A)",
        help="Use this field if the church of the partner"
             " can not correctly be determined and linked.")
    deathdate = fields.Date('Death date')
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
    abroad = fields.Boolean(
        'Abroad/Only e-mail',
        related='email_only',
        help="Indicates if the partner is abroad and should only be "
             "updated by e-mail")
    photo_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='both',
        required=True,
        help='Delivery preference for Child photo')

    partner_duplicate_ids = fields.Many2many(
        'res.partner', 'res_partner_duplicates', 'partner_id',
        'duplicate_id', readonly=True)
    church_member_count = fields.Integer(compute='_compute_is_church',
                                         store=True)

    ambassador_details_id = fields.Many2one('ambassador.details',
                                            'Details of ambassador')
    # TODO Delete these fields after production migration
    ambassador_quote = fields.Text(
        readonly=True,
        help='Old ambassador quote field kept for migration purpose.'
             'Not used anymore')
    quote_migrated = fields.Boolean()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('category_id', 'member_ids')
    def _compute_is_church(self):
        """ Tell if the given Partners are Church Partners
            (by looking at their categories). """

        # Retrieve all the categories and check if one is Church
        church_category = self.env['res.partner.category'].with_context(
            lang='en_US').search([('name', '=', 'Church')], limit=1)
        for record in self:
            is_church = False
            if church_category in record.category_id:
                is_church = True

            record.church_member_count = len(record.member_ids)
            record.is_church = is_church

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

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """
        Lookup for duplicate partners and notify.
        """
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
        partner = super(ResPartner, self).create(vals)
        partner.compute_geopoint()

        return partner

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        """Extends to look on firstname and reference."""
        if args is None:
            args = []
        ids = []
        if name:
            values = name.split(' ')
            if len(values) == 1:
                # Search only ref or full name
                tmp_ids = self.search(
                    [('ref', '=', name)] + args,
                    limit=limit
                )
                if tmp_ids:
                    ids += tmp_ids.ids
                else:
                    tmp_ids = self.search(
                        [('name', 'ilike', name)] + args,
                        limit=limit
                    )
                    if tmp_ids:
                        ids += tmp_ids.ids
            else:
                # Search lastname and firstname
                lastname_ids = self.search(
                    [('lastname', 'ilike', values[0])] + args,
                )
                if lastname_ids:
                    ids += lastname_ids.ids
                firstname_ids = self.search(
                    [('firstname', 'ilike', values[1]),
                     ('id', 'in', lastname_ids.ids)] + args,
                )
                if firstname_ids:
                    # Give more weight two those who has both results
                    ids = firstname_ids.ids
                if not ids:
                    ids = self.search(
                        [('name', 'ilike', name)] + args,
                        limit=limit
                    ).ids
        else:
            ids = self.search(
                args,
                limit=limit
            ).ids
        # we sort by occurence
        to_ret_ids = list(set(ids))
        to_ret_ids = sorted(
            to_ret_ids,
            key=lambda x: ids.count(x),
            reverse=True
        )[:limit]
        return self.browse(to_ret_ids).name_get()

    ##########################################################################
    #                             ONCHANGE METHODS                           #
    ##########################################################################
    @api.onchange('lastname', 'firstname', 'zip', 'email')
    def _onchange_partner(self):
        if (self.lastname and self.firstname and self.zip) or self.email:
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
            partner.write({'geo_point': geo_point.wkt})
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
        bvr_reference += '0' * (4 - len(product.fund_id)) + product.fund_id
        bvr_reference += '0' * 4
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
    def open_sponsored_children(self):
        self.ensure_one()
        if self.is_church:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Children',
                'res_model': 'compassion.child',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': ['|', ('sponsor_id', '=', self.id),
                           ('sponsor_id', 'in', self.member_ids.ids)],
                'context': self.env.context,
            }
        else:
            return super(ResPartner, self).open_sponsored_children()

    @api.multi
    def open_contracts(self):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
        self.ensure_one()
        if self.is_church:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contracts',
                'res_model': 'recurring.contract',
                'views': [[False, "tree"], [False, "form"]],
                'domain': ['|', '|',
                           ('correspondent_id', 'in', self.member_ids.ids),
                           ('correspondent_id', '=', self.id), '|',
                           ('partner_id', '=', self.id),
                           ('partner_id', 'in', self.member_ids.ids)],
                'context': self.with_context({
                    'default_type': 'S',
                    'search_default_active': True
                }).env.context,
            }
        else:
            return super(ResPartner, self).open_contracts()

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS)

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

    def update_church_sponsorships_number(self):
        """
        Update the count of sponsorships for the church of the partner
        :return: True
        """
        return self.mapped('church_id').update_number_sponsorships()

    def update_number_sponsorships(self):
        """
        Includes church members sponsorships in the count
        :return: True
        """
        for partner in self:
            partner.number_sponsorships = self.env[
                'recurring.contract'].search_count([
                    '|', '|',
                    ('correspondent_id', 'in', partner.member_ids.ids),
                    ('correspondent_id', '=', partner.id), '|',
                    ('partner_id', '=', partner.id),
                    ('partner_id', 'in', partner.member_ids.ids),
                    ('state', 'not in', ['cancelled', 'terminated']),
                    ('child_id', '!=', False),
                    ('activation_date', '!=', False),
                ])
        return True
