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
from openerp.osv import orm
from . import gp_connector


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """

    _inherit = 'res.partner'

    def _get_receipt_types(self, cursor, uid, context=None):
        """ Display values for the receipt selection fields. """
        return [
            ('no', _('No receipt')),
            ('default', _('Default')),
            ('email', _('By e-mail')),
            ('paper', _('On paper'))]

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    # ########################################################################
    ref = fields.Char(default=False)
    lang = fields.Selection(default=False)
    opt_out = fields.Boolean(default=True)
    nbmag = fields.integer('Number of Magazines', size=2,
                           required=True, default=0)
    tax_certificate = fields.selection(
        _get_receipt_types, required=True, default='default')
    thankyou_letter = fields.selection(
        _get_receipt_types, _('Thank you letter'),
        required=True, default='default')
    calendar = fields.boolean(
        help=_("Indicates if the partner wants to receive the Compassion "
               "calendar."), default=True)
    christmas_card = fields.boolean(
        help=_("Indicates if the partner wants to receive the "
               "christmas card."), default=True)
    birthday_reminder = fields.boolean(
        help=_("Indicates if the partner wants to receive a birthday "
               "reminder of his child."), default=True)
    abroad = fields.boolean(
        'Abroad/Only e-mail',
        help=_("Indicates if the partner is abroad and should only be "
               "updated by e-mail"))

    ##########################################################################
    #                           PUBLIC METHODS                               #
    ##########################################################################
    def create_from_gp(self, cr, uid, vals, context=None):
        """ Simple create method that skips MySQL insertion, since it is
            called from GP in order to export the addresses. """
        return super(ResPartner, self).create(cr, uid, vals, context)

    def write_from_gp(self, cr, uid, ids, vals, context=None):
        """ Simple write method that skips MySQL insertion, since it is
        called from GP in order to export the addresses. """
        return super(ResPartner, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context=None):
        """ We override the create method so that each partner creation will
            also propagate in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the Odoo holds all the logic
            to sync the two databases.
        """
        gp = gp_connector.GPConnect()
        fieldsUpdate = vals.keys()

        # If the reference is not defined, we automatically set it.
        if 'ref' not in fieldsUpdate:
            # If the contact has a parent and uses his address, plus the parent
            # has a reference, we use the same reference.
            if vals.get('parent_id') and vals.get('use_parent_address'):
                vals['ref'] = self.browse(
                    cr, uid, vals['parent_id'], context=context).ref
            # Otherwise we attribute a new reference number
            else:
                vals['ref'] = gp.nextRef()

        # Create the partner in Odoo, with original values, before exporting
        # to MySQL.
        new_id = super(ResPartner, self).create(cr, uid, vals, context)
        partner = self.browse(cr, uid, new_id, {'lang': 'en_US'})

        # Set some special fields that need a conversion before sending to
        # MySQL
        categories = self._get_category_names(partner, cr, uid)
        self._update_vals_with_gp_partner(partner, vals)

        gp.createPartner(uid, vals, partner, categories)

        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        """ We override the write method so that each update will also update
            the partner in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the update syncs the two
            databases. """
        # We first call the original write method and update the records.
        result = super(ResPartner, self).write(
            cr, uid, ids, vals, context=context)

        # Some fields that need some conversion before sending to MySQL
        categories = list()

        records = self.browse(cr, uid, ids, {'lang': 'en_US'})
        records = [records] if not isinstance(records, list) else records
        create = False
        gp = gp_connector.GPConnect()

        for record in records:
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
                            self._get_category_names(record.parent_id, cr,
                                                     uid))
                        # Link with contact in GP and sync or create new
                        # contact if it doesn't exist.
                        ref = gp.getRefContact(record.id)
                        if ref < 0:
                            ref = str(gp.nextRef())
                            create = True
                        vals['ref'] = ref
                    # Write the new reference in OpenERP
                    super(ResPartner, self).write(
                        cr, uid, record.id, vals, context)
                    record.ref = vals['ref']
                    # We need to copy all partner fields in the new referenced
                    # partner in MySQL
                    self._fill_fields(record, vals)

                # Handle the change of the company status (weird update, but
                # could happen!)
                if 'is_company' in vals.keys():
                    if vals['is_company']:
                        gp.changeToCompany(uid, record.id, record.name)
                    else:
                        # Unlink the contact, if any exists.
                        gp.unlinkContact(
                            uid, record,
                            self._get_category_names(record, cr, uid))
                        gp.changeToPrivate(uid, record.id)
                        # Add name information to contact
                        vals['lastname'] = record.lastname
            else:
                # The partner has no relation to MySQL ! Fix it.
                self._fill_fields(record, vals)
                ref = gp.getRefContact(record.id)
                if ref < 0:
                    ref = str(gp.nextRef())
                    create = True
                vals['ref'] = ref
                # Write the new reference in OpenERP
                record.ref = ref
                super(ResPartner, self).write(
                    cr, uid, record.id, vals, context=context)

            # Get the special fields values
            categories = self._get_category_names(record, cr, uid)

            # Update the MySQL table with the retrieved values.
            self._update_vals_with_gp_partner(record, vals)
            if create:
                gp.createPartner(uid, vals, record, categories)
            else:
                gp.updatePartner(uid, vals, record, categories)

        return result

    def unlink(self, cr, uid, ids, context=None):
        """ We want to perform some checks before deleting a partner ! """
        records = self.browse(cr, uid, ids, context)
        records = [records] if not isinstance(records, list) else records
        gp = gp_connector.GPConnect()
        for record in records:
            # If it is a company, unlink contact in MySQL if there is any.
            if record.is_company:
                for child in record.child_ids:
                    if child.use_parent_address:
                        gp.unlinkContact(
                            uid, record, self._get_category_names(record, cr,
                                                                  uid))

            # If it is a contact, unlink from company.
            if record.use_parent_address and record.parent_id:
                gp.unlinkContact(
                    uid, record.parent_id, self._get_category_names(
                        record.parent_id, cr, uid))

            # Unlink from MySQL
            gp.unlink(uid, record.id)

        return super(ResPartner, self).unlink(cr, uid, ids, context)

    def get_unreconciled_amount(self, cr, uid, partner_id, context=None):
        """Returns the amount of unreconciled credits in Account 1050"""
        partner = self._find_accounting_partner(self.browse(
            cr, uid, partner_id, context))
        mv_line_obj = self.pool.get('account.move.line')
        move_line_ids = mv_line_obj.search(cr, uid, [
            ('partner_id', '=', partner.id),
            ('account_id.code', '=', '1050'),
            ('credit', '>', '0'),
            ('reconcile_id', '=', False)], context=context)
        res = 0
        for move_line in mv_line_obj.browse(cr, uid, move_line_ids, context):
            res += move_line.credit
        return res

    ##########################################################################
    #                           PRIVATE METHODS                              #
    ##########################################################################
    def _update_vals_with_gp_partner(self, partner, vals):
        """ Updates the vals dictionary with correct values for GP
        given the type of the partner (company / contact). """
        count = 0

        # By default, update the GP partner with erp_id = partner.id
        vals['id'] = partner.id

        # Don't unset the "Mailing complet" category when the parent wants to
        # receive it.
        if partner.use_parent_address and not partner.parent_id.opt_out and \
           'opt_out' in vals:
            del vals['opt_out']

        # Check if the record is a company with children and update fields
        # accordingly.
        for child_record in partner.child_ids:
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
            raise orm.except_orm(
                _("Partner Error"),
                _("You cannot more than one contact with same address than "
                  "the company. GP does not handle that!"))

    def _get_category_names(self, record, cr, uid, context={'lang': 'en_US'}):
        """ Get a list of the category names of all linked partners.

        Args:
            record (res.partner) : The current partner for which we search
                                   the categories

        Returns:
            A list of strings containing the category names of the current
            partner, his parent and children.
        """
        categories = []
        ids = map(lambda category: category.id, record.category_id)
        category_obj = self.pool.get('res.partner.category')
        for category in category_obj.browse(cr, uid, ids, context):
            categories.append(category.name)
        if record.use_parent_address and record.parent_id:
            for category in category_obj.browse(cr, uid,
                                                record.parent_id.category_id,
                                                context):
                categories.append(category.id.name)
        for child_record in record.child_ids:
            if child_record.use_parent_address:
                for category in category_obj.browse(cr, uid,
                                                    child_record.category_id,
                                                    context):
                    categories.append(category.id.name)
        return categories

    def _fill_fields(self, record, vals):
        """ Fills all needed vals for the MySQL table. """
        vals['title'] = record.title.id
        vals['lang'] = record.lang
        vals['firstname'] = record.firstname
        vals['lastname'] = record.lastname
        vals['function'] = record.function
        vals['nbmag'] = record.nbmag
        vals['calendar'] = record.calendar
        vals['tax_certificate'] = record.tax_certificate
        vals['thankyou_letter'] = record.thankyou_letter
        vals['abroad'] = record.abroad
        vals['opt_out'] = record.opt_out
        vals['mobile'] = record.mobile
        vals['category_id'] = record.category_id
        if not record.use_parent_address:
            # Creation of new partner, add all possible fields.
            vals['street'] = record.street
            vals['street2'] = record.street2
            vals['street3'] = record.street3
            vals['city'] = record.city
            vals['zip'] = record.zip
            vals['country_id'] = record.country_id.id
            vals['birthdate'] = record.birthdate
            vals['deathdate'] = record.deathdate
            vals['phone'] = record.phone
            vals['email'] = record.email
            vals['church_id'] = record.church_id.id
            vals['church_unlinked'] = record.church_unlinked
            vals['date'] = record.date
