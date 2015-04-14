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

    # return all child information for all childs from a partner_id specified
    def get_children_from_partner(self, cr, uid, partner_id, context=None):

        # get the Singleton instance of the recurring.contract model from the
        # registry pool for the database in use
        contract_obj = self.pool.get('recurring.contract')

        # get all contract_id from a partner_id
        contract_ids = contract_obj.search(
            cr, uid, [('partner_id', '=', partner_id)], context=None)

        # get all child informations from each contract_id for each child
        children = list()
        for contract in contract_obj.browse(cr, uid, contract_ids, context):
            #contract must be linked to a child
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
