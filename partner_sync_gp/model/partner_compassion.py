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
from openerp import api, models
from . import gp_connector


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """

    _inherit = 'res.partner'

    ##########################################################################
    #                           PUBLIC METHODS                               #
    ##########################################################################
    @api.model
    def gp_create(self, vals):
        """ Simple create method that skips MySQL insertion, since it is
            called from GP in order to export the addresses. """
        for key in vals.iterkeys():
            if key.endswith('_id'):
                vals[key] = int(vals[key])
        partner = super(ResPartner, self).create(vals)
        return partner.id

    @api.multi
    def gp_write(self, vals):
        """ Simple write method that skips MySQL insertion, since it is
        called from GP in order to export the addresses, and to cast
        integers which are not properly passed by GP. """
        for key in vals.iterkeys():
            if key.endswith('_id'):
                vals[key] = int(vals[key])
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
        gp.upsert_partner(partner, categories, uid)

        return partner

    @api.multi
    def write(self, vals):
        """ We override the write method so that each update will also update
            the partner in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the update syncs the two
            databases. """
        uid = self.env.user.id
        gp = gp_connector.GPConnect()

        # We first call the original write method and update the records.
        result = super(ResPartner, self).write(vals)

        for partner in self.with_context(lang='en_US'):
            if partner.ref:
                # Handle the change of parent_id and use_parent_address
                if 'use_parent_address' in vals.keys() and partner.parent_id:
                    if vals['use_parent_address']:
                        # Change the MySQL partner so that it is linked to the
                        # contact
                        gp.linkContact(uid, partner.parent_id.ref, partner.id)
                        # Merge contact with parent
                        vals['ref'] = partner.parent_id.ref
                    else:
                        # Change the MySQL company partner so that it is no
                        # more linked to the contact of the company
                        gp.unlinkContact(
                            uid, partner.parent_id,
                            partner.parent_id._get_category_names())
                        # Link with contact in GP and sync or create new
                        # contact if it doesn't exist.
                        ref = gp.getRefContact(uid, partner.id)
                        if ref < 0:
                            ref = str(gp.nextRef())
                        vals['ref'] = ref
                    # Write the new reference in OpenERP
                    partner.ref = vals['ref']

                # Handle the change of the company status (weird update, but
                # could happen!)
                if 'is_company' in vals.keys():
                    if vals['is_company']:
                        gp.changeToCompany(uid, partner.id, partner.name)
                    else:
                        # Unlink the contact, if any exists.
                        gp.unlinkContact(
                            uid, partner, partner._get_category_names())
                        gp.changeToPrivate(uid, partner.id)
                        # Add name information to contact
            else:
                # The partner has no relation to MySQL ! Fix it.
                ref = gp.getRefContact(partner.id)
                if ref < 0:
                    ref = str(gp.nextRef())
                # Write the new reference in OpenERP
                partner.ref = ref

            # Get the special fields values
            categories = partner._get_category_names()
            gp.upsert_partner(partner, categories, uid)

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

    ##########################################################################
    #                           PRIVATE METHODS                              #
    ##########################################################################
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
