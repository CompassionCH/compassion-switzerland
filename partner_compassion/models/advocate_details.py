
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from datetime import datetime

from odoo import api, fields, _
from odoo.tools import file_open

from odoo.addons.base_geoengine import geo_model
from odoo.addons.base_geoengine import fields as geo_fields

_logger = logging.getLogger(__name__)

try:
    from pandas.tseries.offsets import BDay
except ImportError:
    _logger.warning("Please install pandas for the Advocate CRON to work")


class AdvocateDetails(geo_model.GeoModel):
    _name = "advocate.details"
    _description = "Advocate Details"
    _rec_name = "partner_id"
    _inherit = "mail.thread"

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete='cascade')
    description = fields.Text(translate=False)
    quote = fields.Text(translate=False)
    picture_large = fields.Binary(
        string='Large picture', attachment=True,
        help='Optional large picture for your profile page'
    )
    picture_filename = fields.Char(compute='_compute_filename')
    thank_you_quote = fields.Html(
        compute='_compute_thank_you_quote',
        help='Used in thank you letters for donations linked to an event '
             'and to this partner.',
    )
    mail_copy_when_donation = fields.Boolean()
    number_surveys = fields.Integer(related='partner_id.survey_input_count')

    # Advocacy fields
    #################
    active_since = fields.Date()
    end_date = fields.Date()
    last_event = fields.Date(compute='_compute_events')
    state = fields.Selection([
        ('new', 'New advocate'),
        ('active', 'Active'),
        ('on_break', 'On break'),
        ('inactive', 'Inactive'),
    ], default='new', required=True, track_visibility='onchange')
    break_end = fields.Date()
    advocacy_source = fields.Text(
        help='Describe how this advocate has partnered with us.'
    )
    has_car = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], 'Has a car')
    formation_ids = fields.Many2many(
        'calendar.event', string='Formation taken',
        compute='_compute_formation', inverse='_inverse_formation',
        groups="base.group_user"
    )
    engagement_ids = fields.Many2many(
        'advocate.engagement', 'advocate_engagement_rel',
        'advocate_details_id', 'engagement_id', 'Engagement type'
    )
    t_shirt_size = fields.Selection([
        ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'),
        ('XXL', 'XXL')
    ])
    t_shirt_type = fields.Selection([
        ('shirt', 'Shirt'),
        ('bikeshirt', 'Bikeshirt'),
    ])
    event_ids = fields.Many2many(
        'crm.event.compassion', string='Events', compute='_compute_events'
    )
    event_type_formation = fields.Integer(compute='_compute_formation')
    number_events = fields.Integer(compute='_compute_events')

    # Partner related fields
    ########################
    birthdate = fields.Date(
        related='partner_id.birthdate_date', store=True, readonly=True)
    lang = fields.Selection(
        related='partner_id.lang', store=True, readonly=True)
    zip = fields.Char(
        related='partner_id.zip', store=True, readonly=True)
    city = fields.Char(
        related='partner_id.city', store=True, readonly=True)
    email = fields.Char(
        related='partner_id.email', store=True, readonly=True)
    geo_point = geo_fields.GeoPoint(readonly=True)

    _sql_constraints = [
        ('details_unique', 'unique(partner_id)',
         'Only one details per ambassador is allowed!')
    ]

    @api.multi
    def _compute_filename(self):
        for details in self:
            partner_name = details.display_name
            details.picture_filename = partner_name + '-large.jpg'

    @api.multi
    def _compute_thank_you_quote(self):
        html_file = file_open(
            'partner_compassion/static/src/html/thank_you_quote_template.html')
        template_html = str(html_file.read())
        for details in self:
            firstname = details.partner_id.firstname
            lastname = details.partner_id.lastname
            html_vals = {
                'img_alt': details.display_name,
                'image_data': details.partner_id.with_context(
                    bin_size=False).image,
                'text': details.quote or '',
                'attribution': _(f'Quote from {firstname} {lastname}')
                if details.quote else '',
            }
            details.thank_you_quote = template_html.format(**html_vals)

    @api.multi
    def _compute_events(self):
        for details in self:
            details.event_ids = self.env['crm.event.compassion'].search([
                ('staff_ids', '=', details.partner_id.id),
                ('end_date', '<', fields.Datetime.now())
            ])
            details.number_events = len(details.event_ids)
            details.last_event = details.event_ids[:1].end_date

    @api.multi
    def _compute_formation(self):
        formation_cated_id = self.env.ref(
            'partner_compassion.event_type_formation').id
        for details in self:
            details.formation_ids = self.env['calendar.event'].search([
                ('partner_ids', '=', details.partner_id.id),
                ('categ_ids', '=', formation_cated_id)
            ])
            details.event_type_formation = formation_cated_id

    @api.multi
    def _inverse_formation(self):
        # Allows to create formation event from ambassador details
        return True

    @api.multi
    def set_geo_point(self):
        for advocate in self:
            advocate.geo_point = advocate.partner_id.geo_point

    @api.model
    def create(self, vals):
        # Link partner to the advocate details
        advocate = super().create(vals)
        advocate.partner_id.advocate_details_id = advocate
        advocate.set_geo_point()
        return advocate

    @api.multi
    def open_events(self):
        return {
            'name': _('Events'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.event.compassion',
            'target': 'current',
            'domain': [('id', 'in', self.event_ids.ids)],
        }

    @api.multi
    def open_surveys(self):
        return {
            'name': _('Surveys'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'target': 'current',
            'domain': [('partner_id', '=', self.partner_id.id)],
        }

    def set_on_break(self):
        self.env.user.notify_info(
            _("Please don't forget to put a break end date"), sticky=True)
        return self.write({'state': 'on_break'})

    def set_inactive(self):
        return self.write({
            'state': 'inactive',
            'end_date': fields.Date.today()
        })

    def set_active(self):
        return self.write({
            'state': 'active',
            'end_date': False,
            'break_end': False
        })

    @api.model
    def advocate_cron(self):
        three_open_days = datetime.today() + BDay(3)
        birthday_advocates = self.search([
            ('state', 'in', ['active', 'on_break']),
            ('birthdate', 'like', three_open_days.strftime('%m-%d'))
        ])
        birthday_advocates = birthday_advocates.filtered(
            lambda a: a.engagement_ids != self.env.ref(
                "partner_compassion.engagement_sport"))
        for advocate in birthday_advocates:
            lang = advocate.partner_id.lang[:2]
            notify_partner_id = self.env['staff.notification.settings'].\
                get_param(f'advocate_birthday_{lang}_id')
            preferred_name = advocate.partner_id.preferred_name
            date = advocate.partner_id.get_date('birthdate_date', '%d %B')
            display_name = advocate.display_name
            advocate.message_post(
                body=_(f"This is a reminder that {preferred_name} "
                       f"will have birthday on {date}."),
                subject=_(f"[{display_name}] Advocate birthday reminder"),
                partner_ids=[notify_partner_id],
                type='comment',
                subtype='mail.mt_comment',
                content_subtype='html'
            )
        break_advocates = self.search([
            ('state', '=', 'on_break'),
            ('break_end', '<', fields.Date.today()),
            ('break_end', '!=', False)
        ])
        break_advocates.set_active()
