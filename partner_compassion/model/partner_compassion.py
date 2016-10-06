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
            ('email', _('By e-mail')),
            ('paper', _('On paper'))]

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    lang = fields.Selection(default=False)
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
        help=_("Indicates if the partner is abroad and should only be "
               "updated by e-mail"))

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
            ('reconcile_id', '=', False)])
        res = 0
        for move_line in move_line_ids:
            res += move_line.credit
        return res

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
    def _display_address(self, address, without_company=False):
        """ Build and return an address formatted accordingly to
        Compassion standards.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country
                  habits (or the default ones if not country is specified)
        :rtype: string
        """

        # get the information that will be injected into the display format
        # get the address format
        address_format = "%(street)s\n%(street2)s\n%(street3)s\n%(city)s " \
                         "%(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code':
            address.country_id and address.country_id.code or '',
            'country_name':
            address.country_id and address.country_id.name or '',
            'company_name':
            address.parent_id and address.parent_id.name or '',
        }

        for field in ADDRESS_FIELDS:
            args[field] = getattr(address, field) or ''

        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args
