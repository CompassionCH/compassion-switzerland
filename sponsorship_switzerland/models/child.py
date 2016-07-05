# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields


class CompassionChild(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'compassion.child'

    old_values = fields.Char(compute='_compute_revised_values')
    old_firstname = fields.Char(compute='_compute_revised_values')
    current_values = fields.Char(compute='_compute_revised_values')

    def _compute_revised_values(self):
        for child in self:
            child.old_values = ', '.join(child.revised_value_ids.mapped(
                'old_value'))
            child.current_values = child.revised_value_ids.get_field_value()
            child.old_firstname = child.revised_value_ids.filtered(
                lambda c: c.name == 'First Name').old_value or child.firstname

    def _major_revision(self, vals):
        """ Private method when a major revision is received for a child.
            Send a communication to the sponsor.
        """
        super(CompassionChild, self)._major_revision(vals)
        if self.revised_value_ids:
            if len(self.revised_value_ids) == 1:
                communication = self.env[
                    'partner.communication.config'].search([
                        ('name', 'ilike', self.revised_value_ids.name),
                        ('name', 'like', 'Major Revision'),
                    ])
            else:
                communication = self.env.ref(
                    'sponsorship_switzerland.major_revision_multiple')
            if communication and self.sponsor_id:
                communication.inform_sponsor(self.sponsor_id, self.id)
