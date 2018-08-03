# -*- coding: utf-8 -*-
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

from odoo import api, models, fields, _
from odoo.tools import file_open

_logger = logging.getLogger(__name__)

try:
    from pandas.tseries.offsets import BDay
except ImportError:
    _logger.warning("Please install pandas for the Advocate CRON to work")


class AmbassadorDetails(models.Model):
    _name = "ambassador.details"
    _description = "Ambassador Details"
    _rec_name = "partner_id"
    _inherit = "mail.thread"

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete='cascade')
    description = fields.Text(translate=True)
    quote = fields.Text(translate=True)
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
    birthdate = fields.Date(
        related='partner_id.birthdate_date', store=True, readonly=True)
    lang = fields.Selection(
        related='partner_id.lang', store=True, readonly=True)
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
    has_car = fields.Selection('_yes_no_selection', 'Has a car')
    formation_ids = fields.Many2many(
        'calendar.event', string='Formation taken',
        compute='_compute_formation', inverse='_inverse_formation',
        groups="base.group_user"
    )
    engagement_ids = fields.Many2many(
        'ambassador.engagement', 'ambassador_engagement_rel',
        'ambassador_details_id', 'engagement_id', 'Engagement type',
        groups="base.group_user"
    )
    t_shirt_size = fields.Selection([
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'),
        ('XXL', 'XXL')
    ])
    event_ids = fields.Many2many(
        'crm.event.compassion', string='Events', compute='_compute_events'
    )
    event_type_formation = fields.Integer(compute='_compute_formation')
    number_events = fields.Integer(compute='_compute_events')

    _sql_constraints = [
        ('details_unique', 'unique(partner_id)',
         'Only one details per ambassador is allowed!')
    ]

    @api.model
    def _yes_no_selection(self):
        return [
            ('yes', 'Yes'),
            ('no', 'No')
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
        template_html = unicode(html_file.read())
        for details in self:
            html_vals = {
                u'img_alt': details.display_name,
                u'image_data': details.partner_id.with_context(
                    bin_size=False).image,
                u'text': details.quote
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
            ('partner_id.category_id', 'ilike', 'advocate'),
            ('birthdate', 'like', three_open_days.strftime('%m-%d'))
        ])
        for advocate in birthday_advocates:
            notify_partner_id = self.env['staff.notification.settings'].\
                get_param(
                'advocate_birthday_{}_id'.format(advocate.partner_id.lang[:2])
                )
            advocate.message_post(
                body=_(u"This is a reminder that {} will have birthday on {}.")
                .format(advocate.partner_id.preferred_name,
                        advocate.partner_id.get_date(
                            'birthdate_date', 'date_month')),
                subject=_(u"[{}] Advocate birthday reminder").format(
                    advocate.display_name),
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
