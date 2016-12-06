# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer <heerphilippe@msn.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields


class ChildLifecycle(models.Model):
    """ Send Communication when Child Lifecycle Event is received. """
    _inherit = 'compassion.child.ble'

    gender = fields.Selection(related='child_id.gender')

    @api.model
    def process_commkit(self, commkit_data):
        ids = super(ChildLifecycle, self).process_commkit(commkit_data)
        for lifecycle in self.browse(ids).filtered('child_id.sponsor_id'):
            communication_type = self.env[
                'partner.communication.config'].search([
                    ('name', 'ilike', lifecycle.type),
                    ('name', 'like', 'Beneficiary'),
                ])
            if communication_type:
                self.env['partner.communication.job'].create({
                    'config_id': communication_type.id,
                    'partner_id': lifecycle.child_id.sponsor_id.id,
                    'object_ids': lifecycle.child_id.id,
                })
        return ids


class ProjectLifecycle(models.Model):
    """ Send Communication when icp lifecycle is received. """
    _inherit = 'compassion.project.ile'

    @api.model
    def process_commkit(self, commkit_data):
        ids = super(ProjectLifecycle, self).process_commkit(commkit_data)

        for lifecycle in self.browse(ids):
            if lifecycle.type == 'Reactivation' or \
                    lifecycle.type == 'Suspension':

                for child in self.env['compassion.child'].\
                        search([('project_id', '=', lifecycle.project_id.id),
                                ('sponsor_id', '!=', False)]):
                    communication_type = self.env.ref(
                        'partner_communication_switzerland.project_lifecycle')
                    self.env['partner.communication.job'].create({
                        'config_id': communication_type.id,
                        'partner_id': child.sponsor_id.id,
                        'object_ids': child.id,
                    })
        return ids
