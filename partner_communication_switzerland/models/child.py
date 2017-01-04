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
import locale

from openerp import api, models, fields, _


def major_revision(child, revised_values):
    """ Finds the correct communication to send. """
    if len(revised_values) == 1:
        communication_type = child.env['partner.communication.config'].search([
            ('name', 'ilike', revised_values.name),
            ('name', 'like', 'Major Revision'),
        ])
    else:
        communication_type = child.env.ref(
            'partner_communication_switzerland.major_revision_multiple')
    if communication_type:
        child.env['partner.communication.job'].create({
            'config_id': communication_type.id,
            'partner_id': child.sponsor_id.id,
            'object_ids': child.id,
        })


class CompassionChild(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'compassion.child'

    old_values = fields.Char(compute='_compute_revised_values')
    old_firstname = fields.Char(compute='_compute_revised_values')
    current_values = fields.Char(compute='_compute_revised_values')
    birthday_month = fields.Char(compute='_compute_birthday_month')
    completion_month = fields.Char(compute='_compute_completion_month')

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
            major_revision(self, self.revised_value_ids)

    def _compute_birthday_month(self):
        """ Gets the birthday month in full text. """
        current_locale = '.'.join(locale.getlocale())
        lang = self.env.lang.encode('ascii')
        locale.setlocale(locale.LC_TIME, lang + '.UTF-8')
        for child in self:
            birthday = fields.Date.from_string(child.birthdate)
            child.birthday_month = birthday.strftime("%B")
        locale.setlocale(locale.LC_TIME, current_locale)

    def _compute_completion_month(self):
        """ Completion month in full text. """
        current_locale = '.'.join(locale.getlocale())
        lang = self.env.lang.encode('ascii')
        locale.setlocale(locale.LC_TIME, lang + '.UTF-8')
        for child in self:
            completion = fields.Date.from_string(child.completion_date)
            child.completion_month = completion.strftime("%B")
        locale.setlocale(locale.LC_TIME, current_locale)

    def depart(self):
        """ Send communication to sponsor. """
        for child in self.filtered('sponsor_id'):
            if child.lifecycle_ids[0].type == 'Planned Exit':
                communication_type = self.env.ref(
                    'partner_communication_switzerland.'
                    'lifecycle_child_planned_exit')
            else:
                communication_type = self.env.ref(
                    'partner_communication_switzerland.'
                    'lifecycle_child_unplanned_exit')
            self.env['partner.communication.job'].create({
                'config_id': communication_type.id,
                'partner_id': child.sponsor_id.id,
                'object_ids': child.id,
            })
        super(CompassionChild, self).depart()

    def reinstatement(self):
        """ Send communication to sponsor. """
        communication_type = self.env.ref(
            'partner_communication_switzerland.lifecycle_child_reinstatement')
        for child in self.filtered('sponsorship_ids'):
            self.env['partner.communication.job'].create({
                'config_id': communication_type.id,
                'partner_id': child.sponsorship_ids[0].correspondant_id.id,
                'object_ids': child.id,
            })
        super(CompassionChild, self).reinstatement()

    def new_photo(self):
        super(CompassionChild, self).new_photo()
        communication_config = self.env.ref(
            'partner_communication_switzerland.biennial')
        job_obj = self.env['partner.communication.job']
        for child in self.filtered('sponsor_id').filtered('pictures_ids'):
            # In case picture is sent by e-mail, include it in e-mail values
            pictures = child.pictures_ids[0]
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'compassion.child.pictures'),
                ('res_id', '=', pictures.id),
                ('datas_fname', 'like', 'Fullshot')
            ], limit=1)
            job_obj.with_context({
                'default_email_vals': {
                    'attachment_ids': [(6, 0, attachment.ids)]}
            }).create({
                'config_id': communication_config.id,
                'partner_id': child.sponsor_id.id,
                'object_ids': child.id,
            })

    def get_number(self):
        """ Returns a string telling how many children are in the recordset.
        """
        number_dict = {
            1: _("one"),
            2: _("two"),
            3: _("three"),
            4: _("four"),
            5: _("five"),
            6: _("six"),
            7: _("seven"),
            8: _("eight"),
            9: _("nine"),
            10: _("ten"),
        }
        return number_dict.get(len(self), str(len(self))) + ' ' + self.get(
            'child')

    def get_completion(self):
        """ Return the full completion dates. """
        month = self[0].completion_month
        year = fields.Date.from_string(self[0].completion_date).strftime("%Y")
        if not month:
            return year
        return month + ' ' + year


class Household(models.Model):
    """ Send Communication when Household Major Revision is received. """
    _inherit = 'compassion.household'

    def process_commkit(self, commkit_data):
        ids = super(Household, self).process_commkit(commkit_data)
        households = self.browse(ids)
        for household in households:
            if household.revised_value_ids:
                for child in household.child_ids.filtered('sponsor_id'):
                    major_revision(child, self.revised_value_ids)
        return ids


class ChildNotes(models.Model):
    _inherit = 'compassion.child.note'

    @api.model
    def create(self, vals):
        """ Inform sponsor when receiving new Notes. """
        note = super(ChildNotes, self).create(vals)
        child = note.child_id
        if child.sponsor_id:
            communication_config = self.env.ref(
                'partner_communication_switzerland.child_notes')
            self.env['partner.communication.job'].create({
                'config_id': communication_config.id,
                'partner_id': child.sponsor_id.id,
                'object_ids': child.id,
            })
        return note
