# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.tools import mod10r

from openerp import api, fields, models, _

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
    total_invoiced = fields.Float(groups=False)
    street3 = fields.Char("Street3", size=128)
    member_ids = fields.One2many(
        'res.partner', 'church_id', 'Members',
        domain=[('active', '=', True)])
    is_church = fields.Boolean(
        string="Is a Church", compute='_is_church', store=True)
    church_id = fields.Many2one(
        'res.partner', 'Church', domain=[('is_church', '=', True)])
    church_unlinked = fields.Char(
        "Church (N/A)",
        help=_("Use this field if the church of the partner"
               " can not correctly be determined and linked."))
    deathdate = fields.Date('Death date')
    opt_out = fields.Boolean(default=True)
    nbmag = fields.Integer('Number of Magazines', size=2,
                           required=True, default=0)
    tax_certificate = fields.Selection(
        _get_receipt_types, required=True, default='default')
    thankyou_letter = fields.Selection(
        _get_receipt_types, _('Thank you letter'),
        required=True, default='default')
    calendar = fields.Boolean(
        help=_("Indicates if the partner wants to receive the Compassion "
               "calendar."), default=True)
    christmas_card = fields.Boolean(
        help=_("Indicates if the partner wants to receive the "
               "christmas card."), default=True)
    birthday_reminder = fields.Boolean(
        help=_("Indicates if the partner wants to receive a birthday "
               "reminder of his child."), default=True)
    abroad = fields.Boolean(
        'Abroad/Only e-mail',
        related='email_only',
        help=_("Indicates if the partner is abroad and should only be "
               "updated by e-mail"))
    photo_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='both',
        required=True,
        help='Delivery preference for Child photo')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('category_id')
    def _is_church(self):
        """ Tell if the given Partners are Church Partners
            (by looking at their categories). """

        # Retrieve all the categories and check if one is Church
        church_category = self.env['res.partner.category'].with_context(
            lang='en_US').search([('name', '=', 'Church')], limit=1)
        for record in self:
            is_church = False
            if church_category in record.category_id:
                is_church = True
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
        vals['ref'] = self.env['ir.sequence'].get('partner.ref')
        partner = super(ResPartner, self.with_context(
            no_geocode=True)).create(vals)
        if self._can_geocode():
            # Call precise service of localization
            partner.geocode_address()
            if not partner.geo_point:
                # Call approximate service
                partner.geocode_from_geonames()
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
                    )
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
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def compute_geopoint(self):
        """ Compute all geopoints. """
        self.search([
            ('partner_latitude', '!=', False),
            ('partner_longitude', '!=', False),
        ])._get_geo_point()
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
        bvr_reference += '0' * (4 -
                                len(product.fund_id)) + product.fund_id
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
        record = self.get_record_from_phone_number(phone)
        if record:
            partner = self.browse(record[1])
        return record and partner.lang

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS)

    def _can_geocode(self):
        """ Remove approximate geocoding when a precise position is
        already set.
        """
        if 'no_geocode' in self.env.context:
            return False
        return super(ResPartner, self)._can_geocode()
