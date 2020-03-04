##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api
from odoo.addons.website.models.website import slugify as slug
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT


class EventCompassion(models.Model):
    _name = 'crm.event.compassion'
    _inherit = ['crm.event.compassion', 'website.published.mixin',
                'translatable.model', 'website.seo.metadata']

    name = fields.Char(translate=True)
    website_description = fields.Html(translate=True, sanitize=False)
    thank_you_text = fields.Html(translate=True)
    picture_1 = fields.Binary('Banner image', attachment=True)
    filename_1 = fields.Char(compute='_compute_filenames')
    website_side_info = fields.Html(
        string='Side info', translate=True, sanitize=False
    )
    event_type_id = fields.Many2one(
        'event.type', 'Type', required=True,
        # Avoids selecting generic events
        domain=[('id', '>', 1)],
    )
    type = fields.Selection(
        compute='_compute_event_type', default='meeting', store=True)
    odoo_event_id = fields.Many2one('event.event')
    accepts_registrations = fields.Boolean(
        related='event_type_id.accepts_registrations')
    seats_expected = fields.Integer(related='odoo_event_id.seats_expected')

    registrations_closed = fields.Boolean("Close new registrations", default=True)
    registrations_closed_text = fields.Char(
        "Close Registrations Text",
        default="This event has ended",
        translate=True
    )
    registrations_ended = fields.Boolean(compute='_compute_registrations_ended')

    @api.multi
    def _compute_registrations_ended(self):
        for event in self:
            event_end_date = fields.datetime.strptime(event.end_date, DT_FORMAT)
            event.registrations_ended = fields.datetime.now() > event_end_date

    @api.multi
    def _compute_website_url(self):
        for event in self:
            event.website_url = "/event/{}".format(slug(event))

    @api.multi
    def _compute_filenames(self):
        for event in self:
            event.filename_1 = event.name + '-1.jpg'

    @api.multi
    @api.depends('event_type_id')
    def _compute_event_type(self):
        sport = self.env.ref('website_event_compassion.event_type_sport')
        stand = self.env.ref('website_event_compassion.event_type_stand')
        concert = self.env.ref('website_event_compassion.event_type_concert')
        pres = self.env.ref('website_event_compassion.event_type_presentation')
        meeting = self.env.ref('website_event_compassion.event_type_meeting')
        group = self.env.ref('website_event_compassion.event_type_group_visit')
        youth = self.env.ref('website_event_compassion.event_type_youth_trip')
        indiv = self.env.ref(
            'website_event_compassion.event_type_individual_visit')
        for event in self:
            if event.event_type_id == sport:
                event.type = 'sport'
            elif event.event_type_id == stand:
                event.type = 'stand'
            elif event.event_type_id == concert:
                event.type = 'concert'
            elif event.event_type_id == pres:
                event.type = 'presentation'
            elif event.event_type_id == meeting:
                event.type = 'meeting'
            elif event.event_type_id in group | youth | indiv:
                event.type = 'tour'

    def close_registrations(self):
        self.registrations_closed = True

    def open_registrations(self):
        """
        This will create an event.event record and link it to the Compassion
        Event. It's useful for adding participants and managing e-mails
        and participant list.
        :return: action opening the wizard
        """
        self.registrations_closed = False
        if not self.odoo_event_id:
            return {
                'name': 'Open event registrations',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'crm.event.compassion.open.wizard',
                'context': self.env.context,
                'target': 'new',
            }

    def open_participants(self):
        return {
            'name': 'Manage participants',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form,calendar,graph',
            'res_model': 'event.registration',
            'domain': [('event_id', '=', self.odoo_event_id.id)],
            'context': self.with_context(
                default_compassion_event_id=self.id,
                default_event_type_id=self.event_type_id.id,
                default_event_id=self.odoo_event_id.id,
                default_amount_objective=self.odoo_event_id.
                    participants_amount_objective
            ).env.context,
            'target': 'current',
        }

    @api.model
    def past_event_action(self):
        """ Switch partners to "attended" after the event ended """
        for event in self:
            if event.registrations_ended:
                participants = self.env['event.registration'].search([
                    ('event_id', '=', event.odoo_event_id.id)])
                participants.past_event_action()
