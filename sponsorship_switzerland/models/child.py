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


def major_revision(child, revised_values):
    """ Finds the correct communication to send. """
    if len(revised_values) == 1:
        communication = child.env['partner.communication.config'].search([
            ('name', 'ilike', revised_values.name),
            ('name', 'like', 'Major Revision'),
        ])
    else:
        communication = child.env.ref(
            'sponsorship_switzerland.major_revision_multiple')
    if communication:
        communication.inform_sponsor(child.sponsor_id, child.id)


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
            child.old_values = ', '.join(child.revised_value_ids.translate(
                'old_value'))
            child.current_values = child.revised_value_ids.get_field_value()
            child.old_firstname = child.revised_value_ids.filtered(
                lambda c: c.name == 'First Name').old_value or child.firstname

    def _major_revision(self, vals):
        """ Private method when a major revision is received for a child.
            Send a communication to the sponsor.
        """
        super(CompassionChild, self)._major_revision(vals)
        if self.revised_value_ids and self.sponsor_id:
            major_revision(
                self.with_context(lang=self.sponsor_id.lang),
                self.revised_value_ids)


class Household(models.Model):
    """ Send Communication when Household Major Revision is received. """
    _inherit = 'compassion.household'

    def _major_revision(self, vals):
        super(Household, self)._major_revision(vals)
        if self.revised_value_ids:
            for child in self.child_ids:
                if child.sponsor_id:
                    major_revision(
                        child.with_context(lang=child.sponsor_id.lang),
                        self.revised_value_ids)
