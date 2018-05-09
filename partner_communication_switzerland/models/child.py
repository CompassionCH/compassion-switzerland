# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging

from odoo import api, models, fields, _

from odoo.addons.report_compassion.models.contract_group import setlocale

_logger = logging.getLogger(__name__)

try:
    from wand.color import Color
    from wand.drawing import Drawing
    from wand.image import Image
except ImportError:
    _logger.warning("Please install wand.")

# Ratio of white frame around the child picture
FRAME_RATIO = 0.08


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
            'user_id': communication_type.user_id.id,
        })


class CompassionChild(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'compassion.child'

    old_values = fields.Char(compute='_compute_revised_values')
    old_firstname = fields.Char(compute='_compute_revised_values')
    current_values = fields.Char(compute='_compute_revised_values')
    completion_month = fields.Char(compute='_compute_completion_month')
    picture_frame = fields.Binary(compute='_compute_picture_frame')

    def _compute_revised_values(self):
        for child in self:
            child.old_values = child.revised_value_ids.get_list('old_value')
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

    def _compute_completion_month(self):
        """ Completion month in full text. """
        for child in self.filtered('completion_date'):
            lang = child.sponsor_id.lang or self.env.lang or 'en_US'
            completion = fields.Date.from_string(child.completion_date)
            with setlocale(lang):
                child.completion_month = completion.strftime("%B")

    def _compute_picture_frame(self):
        for child in self.filtered('fullshot'):
            try:
                with Image(blob=base64.b64decode(child.fullshot)) as picture:
                    frame_width = int(picture.width * FRAME_RATIO)
                    frame_height = int(picture.height * FRAME_RATIO)
                    picture.frame(Color("#fff"), frame_width, frame_height)
                    with Drawing() as draw:
                        draw.fill_color = Color('#000')
                        draw.text_alignment = 'left'
                        draw.font_size = 20
                        draw.text(
                            frame_width + 50,
                            picture.height - int(frame_height / 1.5),
                            child.local_id + ' ' + child.name)
                        draw(picture)
                        child.picture_frame = base64.b64encode(
                            picture.make_blob())
            except:
                child.picture_frame = False

    @api.multi
    def depart(self):
        """ Send depart communication to sponsor if no sub. """
        for child in self.filtered('sponsor_id'):
            sponsorship = self.env['recurring.contract'].search([
                ('child_id', '=', child.id),
                ('state', 'not in', ['terminated', 'cancelled']),
                ('sds_state', '=', 'no_sub')
            ])
            if not sponsorship:
                continue
            if child.lifecycle_ids[0].type == 'Planned Exit':
                communication_type = self.env.ref(
                    'partner_communication_switzerland.'
                    'lifecycle_child_planned_exit')
            else:
                communication_type = self.env.ref(
                    'partner_communication_switzerland.'
                    'lifecycle_child_unplanned_exit')
            sponsorship.send_communication(communication_type, both=True)
        super(CompassionChild, self).depart()

    @api.multi
    def reinstatement(self):
        """ Send communication to sponsor. """
        communication_type = self.env.ref(
            'partner_communication_switzerland.lifecycle_child_reinstatement')
        for child in self.filtered('sponsorship_ids'):
            self.env['partner.communication.job'].create({
                'config_id': communication_type.id,
                'partner_id': child.sponsorship_ids[0].correspondent_id.id,
                'object_ids': child.id,
                'user_id': communication_type.user_id.id,
            })
        super(CompassionChild, self).reinstatement()

    @api.multi
    def new_photo(self):
        """
        Upon reception of a new child picture :
        - Mark sponsorships for pictures order if delivery is physical
        - Prepare communication for sponsor
        """
        super(CompassionChild, self).new_photo()
        communication_config = self.env.ref(
            'partner_communication_switzerland.biennial')
        job_obj = self.env['partner.communication.job']
        for child in self.filtered(
                lambda r: r.sponsor_id and r.pictures_ids and
                r.sponsorship_ids[0].state in ('active', 'waiting', 'mandate')
        ):
            sponsor = child.sponsor_id
            delivery = sponsor.photo_delivery_preference
            if 'physical' in delivery or delivery == 'both':
                # Mark sponsorship for order the picture
                child.sponsorship_ids[0].order_photo = True

            job_obj.create({
                'config_id': communication_config.id,
                'partner_id': child.sponsor_id.id,
                'object_ids': child.id,
                'user_id': communication_config.user_id.id,
            })
        return True

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

    @api.multi
    def get_hold_gifts(self):
        """
        :return: True if all children's gift are held.
        """
        return reduce(lambda x, y: x and y,
                      self.mapped('project_id.hold_gifts'))


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
                'user_id': communication_config.user_id.id,
            })
        return note
