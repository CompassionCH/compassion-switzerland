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
            if 'S' in contract.type:
                child = {
                    'id': contract.child_id.id,
                    'code': contract.child_id.code,
                    'type': contract.child_id.type,
                    'state': contract.child_id.state,
                    'firstname': contract.child_id.firstname,
                    'name': contract.child_id.name,
                    'gender': contract.child_id.gender,
                    'birthdate': contract.child_id.birthdate,
                    'desc_fr': contract.child_id.desc_fr,
                    'desc_it': contract.child_id.desc_it,
                    'desc_de': contract.child_id.desc_de,
                    'desc_en': contract.child_id.desc_en
                }
                children.append(child)

        return children

    def get_partner_from_user(self, cr, uid, args, context=None):
        """
        Attempt to login with username and password
        return all partner informations and user informations from
        """

        user_obj = self.pool.get('res.users')

        user = user_obj.browse(cr, uid, uid, context)

        partner = {
            'user_id': user.id,
            'login': user.login,
            'partner_id': user.partner_id.id,
            'ref': user.partner_id.ref,
            'title': user.partner_id.title.name,
            'is_company': user.partner_id.is_company,
            'email': user.partner_id.email,
            'phone': user.partner_id.phone,
            'city': user.partner_id.city,
            'zip': user.partner_id.zip,
            'street': user.partner_id.street,
            'street2': user.partner_id.street2,
            'street3': user.partner_id.street3,
            'firstname': user.partner_id.firstname,
            'lastname': user.partner_id.lastname,
            'lang': user.partner_id.lang
        }

        return partner
