# -*- encoding: utf-8 -*-
#
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier
#
#    The licence is in the file __openerp__.py
#

from openerp.osv import orm


class xmlrpc_helper(orm.Model):

    _inherit = "res.partner"

    def get_children_from_partner(self, cr, uid, partner_id, context=None):
        """
        return all child informations for all
        children from a partner_id specified
        """
        contract_obj = self.pool.get('recurring.contract')

        contract_ids = contract_obj.search(
            cr, uid, [('partner_id', '=', partner_id)], context=context)

        # get all child informations from each contract_id for each child
        children = list()
        for contract in contract_obj.browse(cr, uid, contract_ids, context):
            # contract must be linked to a child
            if contract.child_id:
                child = dict()
                child['id'] = contract.child_id.id
                child['code'] = contract.child_id.code
                child['type'] = contract.child_id.type
                child['state'] = contract.child_id.state
                child['firstname'] = contract.child_id.firstname
                child['name'] = contract.child_id.name
                child['gender'] = contract.child_id.gender
                child['birthdate'] = contract.child_id.birthdate
                child['desc_fr'] = contract.child_id.desc_fr
                child['desc_it'] = contract.child_id.desc_it
                child['desc_de'] = contract.child_id.desc_de
                child['desc_en'] = contract.child_id.desc_en
                children.append(child)

        return children

    def get_partner_from_user(self, cr, uid, context=None):
        """
        Attempt to login with username and password
        return all partner informations and user informations from
        """

        user_obj = self.pool.get('res.users')

        user = user_obj.browse(cr, uid, uid, context)

        partner = dict()
        partner['user_id'] = user.id
        partner['login'] = user.login
        partner['partner_id'] = user.partner_id.partner_id
        partner['ref'] = user.partner_id.ref
        partner['title'] = user.partner_id.title
        partner['is_company'] = user.partner_id.is_company
        partner['email'] = user.partner_id.email
        partner['phone'] = user.partner_id.phone
        partner['city'] = user.partner_id.city
        partner['zip'] = user.partner_id.zip
        partner['street'] = user.partner_id.street
        partner['street2'] = user.partner_id.street2
        partner['street3'] = user.partner_id.street3
        partner['firstname'] = user.partner_id.firstname
        partner['lastname'] = user.partner_id.lastname
        partner['lang'] = user.partner_id.lang

        return partner
