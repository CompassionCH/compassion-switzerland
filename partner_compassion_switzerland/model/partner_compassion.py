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
from openerp import api, exceptions, fields, models, _
from . import gp_connector


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
    ref = fields.Char(default=False)
    lang = fields.Selection(default=False)
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
    #                           PUBLIC METHODS                               #
    ##########################################################################
    @api.model
    def create_from_gp(self, vals):
        """ Simple create method that skips MySQL insertion, since it is
            called from GP in order to export the addresses. """
        partner = super(ResPartner, self).create(vals)
        return partner.id

    @api.multi
    def write_from_gp(self, vals):
        """ Simple write method that skips MySQL insertion, since it is
        called from GP in order to export the addresses. """
        return super(ResPartner, self).write(vals)

    @api.model
    def create(self, vals):
        """ We override the create method so that each partner creation will
            also propagate in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the Odoo holds all the logic
            to sync the two databases.
        """
        uid = self.env.user.id
        gp = gp_connector.GPConnect()
        fieldsUpdate = vals.keys()
        obj_partner = self.env['res.partner']
        # If the reference is not defined, we automatically set it.
        if 'ref' not in fieldsUpdate:
            # If the contact has a parent and uses his address, plus the parent
            # has a reference, we use the same reference.
            if vals.get('parent_id') and vals.get('use_parent_address'):
                vals['ref'] = obj_partner.browse(vals['parent_id']).ref
            # Otherwise we attribute a new reference number
            else:
                vals['ref'] = gp.nextRef()

        # Create the partner in Odoo, with original values, before exporting
        # to MySQL.
        partner = super(ResPartner, self).create(
            vals).with_context(lang='en_US')

        # Set some special fields that need a conversion before sending to
        # MySQL
        categories = partner._get_category_names()
        partner._update_vals_with_gp_partner(vals)

        gp.createPartner(uid, vals, partner, categories)

        return partner

    @api.multi
    def write(self, vals):
        """ We override the write method so that each update will also update
            the partner in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the update syncs the two
            databases. """
        uid = self.env.user.id
        # We first call the original write method and update the records.
        result = super(ResPartner, self).write(vals)

        # Some fields that need some conversion before sending to MySQL
        categories = list()

        create = False
        gp = gp_connector.GPConnect()

        for record in self.with_context(lang='en_US'):
            if record.ref:
                # Handle the change of parent_id and use_parent_address
                if 'use_parent_address' in vals.keys() and record.parent_id:
                    if vals['use_parent_address']:
                        # Change the MySQL partner so that it is linked to the
                        # contact
                        gp.linkContact(uid, record.parent_id.ref, record.id)
                        # Merge contact with parent
                        vals['ref'] = record.parent_id.ref
                    else:
                        # Change the MySQL company partner so that it is no
                        # more linked to the contact of the company
                        gp.unlinkContact(
                            uid, record.parent_id,
                            record.parent_id._get_category_names())
                        # Link with contact in GP and sync or create new
                        # contact if it doesn't exist.
                        ref = gp.getRefContact(uid, record.id)
                        if ref < 0:
                            ref = str(gp.nextRef())
                            create = True
                        vals['ref'] = ref
                    # Write the new reference in OpenERP
                    super(ResPartner, record).write(vals)
                    record.ref = vals['ref']
                    # We need to copy all partner fields in the new referenced
                    # partner in MySQL
                    record._fill_fields(vals)

                # Handle the change of the company status (weird update, but
                # could happen!)
                if 'is_company' in vals.keys():
                    if vals['is_company']:
                        gp.changeToCompany(uid, record.id, record.name)
                    else:
                        # Unlink the contact, if any exists.
                        gp.unlinkContact(
                            uid, record, record._get_category_names())
                        gp.changeToPrivate(uid, record.id)
                        # Add name information to contact
                        vals['lastname'] = record.lastname
            else:
                # The partner has no relation to MySQL ! Fix it.
                record._fill_fields(vals)
                ref = gp.getRefContact(record.id)
                if ref < 0:
                    ref = str(gp.nextRef())
                    create = True
                vals['ref'] = ref
                # Write the new reference in OpenERP
                record.ref = ref
                super(ResPartner, record).write(vals)

            # Get the special fields values
            categories = record._get_category_names()

            # Update the MySQL table with the retrieved values.
            record._update_vals_with_gp_partner(vals)
            if create:
                gp.createPartner(uid, vals, record, categories)
            else:
                gp.updatePartner(uid, vals, record, categories)

        return result

    @api.multi
    def unlink(self):
        """ We want to perform some checks before deleting a partner ! """
        uid = self.env.user.id
        gp = gp_connector.GPConnect()
        for record in self:
            # If it is a company, unlink contact in MySQL if there is any.
            if record.is_company:
                for child in record.child_ids:
                    if child.use_parent_address:
                        gp.unlinkContact(
                            uid, record, record._get_category_names())

            # If it is a contact, unlink from company.
            if record.use_parent_address and record.parent_id:
                gp.unlinkContact(
                    uid, record.parent_id,
                    record.parent_id._get_category_names())

            # Unlink from MySQL
            gp.unlink(uid, record.id)

        return super(ResPartner, self).unlink()

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
    #                           PRIVATE METHODS                              #
    ##########################################################################
    @api.one
    def _update_vals_with_gp_partner(self, vals):
        """ Updates the vals dictionary with correct values for GP
        given the type of the partner (company / contact). """
        count = 0

        # By default, update the GP partner with erp_id = partner.id
        vals['id'] = self.id

        # Don't unset the "Mailing complet" category when the parent wants to
        # receive it.
        if self.use_parent_address and not self.parent_id.opt_out and \
           'opt_out' in vals:
            del vals['opt_out']

        # Check if the record is a company with children and update fields
        # accordingly.
        for child_record in self.child_ids:
            if child_record.use_parent_address:
                # Set the correct reference id
                vals['id'] = child_record.id
                # Don't update some values that are defined by the child
                # partner.
                vals.pop('abroad', None)
                vals.pop('opt_out', None)
                vals.pop('thankyou_letter', None)
                vals.pop('tax_certificate', None)
                vals.pop('title', None)
                count += 1
        if count > 1:
            raise exceptions.Warning(
                _("Partner Error"),
                _("You cannot more than one contact with same address than "
                  "the company. GP does not handle that!"))

    def _get_category_names(self):
        """ Get a list of the category names of all linked partners.

        Args:
            record (res.partner) : The current partner for which we search
                                   the categories

        Returns:
            A list of strings containing the category names of the current
            partner, his parent and children.
        """
        categories_name = self.with_context(
            lang='en_US').mapped('category_id.name')

        parent_category_names = self.with_context(lang='en_US').filtered(
            lambda partner: partner.use_parent_address).mapped(
            'parent_id.category_id.name')
        child_category_names = self.with_context(
            lang='en_US').child_ids.filtered(
            lambda partner: partner.use_parent_address).mapped(
                'category_id.name')

        categories_name.extend(parent_category_names)
        categories_name.extend(child_category_names)

        return categories_name

    @api.multi
    def _fill_fields(self, vals):
        """ Fills all needed vals for the MySQL table. """
        self.ensure_one()
        vals['title'] = self.title.id
        vals['lang'] = self.lang
        vals['firstname'] = self.firstname
        vals['lastname'] = self.lastname
        vals['function'] = self.function
        vals['nbmag'] = self.nbmag
        vals['calendar'] = self.calendar
        vals['tax_certificate'] = self.tax_certificate
        vals['thankyou_letter'] = self.thankyou_letter
        vals['abroad'] = self.abroad
        vals['opt_out'] = self.opt_out
        vals['mobile'] = self.mobile
        vals['category_id'] = self.category_id
        if not self.use_parent_address:
            # Creation of new partner, add all possible fields.
            vals['street'] = self.street
            vals['street2'] = self.street2
            vals['street3'] = self.street3
            vals['city'] = self.city
            vals['zip'] = self.zip
            vals['country_id'] = self.country_id.id
            vals['birthdate'] = self.birthdate
            vals['deathdate'] = self.deathdate
            vals['phone'] = self.phone
            vals['email'] = self.email
            vals['church_id'] = self.church_id.id
            vals['church_unlinked'] = self.church_unlinked
            vals['date'] = self.date
