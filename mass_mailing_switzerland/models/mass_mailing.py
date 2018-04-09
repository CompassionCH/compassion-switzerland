# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _

from odoo.addons.queue_job.job import job, related_action


class MassMailing(models.Model):
    """ Add the mailing domain to be viewed in a text field
    """
    _inherit = 'mail.mass_mailing'

    mailing_domain_copy = fields.Char(related='mailing_domain')
    clicks_ratio = fields.Integer(
        compute='_compute_events', store=True, oldname='click_ratio')
    click_event_ids = fields.Many2many(
        'mail.tracking.event', compute='_compute_events')
    unsub_ratio = fields.Integer(
        compute='_compute_events', store=True)
    unsub_event_ids = fields.Many2many(
        'mail.tracking.event', compute='_compute_events')

    _sql_constraints = [('slug_uniq', 'unique (mailing_slug)',
                         'You have to choose a new slug for each mailing !')]

    @api.depends('statistics_ids', 'statistics_ids.tracking_event_ids')
    @job(default_channel='root.mass_mailing_switzerland')
    @related_action('related_action_mass_mailing')
    def _compute_events(self):
        for mass_mail in self.filtered('statistics_ids.tracking_event_ids'):
            has_click = mass_mail.statistics_ids.mapped(
                'tracking_event_ids').filtered(
                lambda e: e.event_type == 'click')
            unsub = mass_mail.statistics_ids.mapped(
                'tracking_event_ids').filtered(
                lambda e: e.event_type == 'unsub')
            mass_mail.click_event_ids = has_click
            mass_mail.unsub_event_ids = unsub
            number_click = len(has_click.mapped(
                'tracking_email_id.mail_stats_id'))
            number_unsub = len(unsub.mapped(
                'tracking_email_id.mail_stats_id'))
            mass_mail.clicks_ratio = 100 * (
                float(number_click) / len(mass_mail.statistics_ids))
            mass_mail.unsub_ratio = 100 * (
                float(number_unsub) / len(mass_mail.statistics_ids))

    @api.multi
    def recompute_events(self):
        self._compute_events()
        return True

    @api.multi
    def send_mail(self):
        # Refresh the sendgrid templates in Odoo
        if self.filtered('email_template_id'):
            self.env['sendgrid.template'].update_templates()
            self.mapped('email_template_id').update_substitutions()

        # Prepare Sendgrid keywords for replacing all urls found
        # in Sendgrid template with tracked URL from Odoo
        emails = self.env['mail.mail']
        mass_mailing_medium_id = self.env.ref(
            'contract_compassion.utm_medium_mass_mailing').id
        for mailing in self:
            substitutions = mailing.mapped(
                'email_template_id.substitution_ids')
            substitutions.replace_tracking_link(
                campaign_id=mailing.mass_mailing_campaign_id.campaign_id.id,
                medium_id=mass_mailing_medium_id,
                source_id=mailing.source_id.id
            )
            emails += super(MassMailing, mailing).send_mail()

        for email in emails:
            # Only update mass mailing state when last e-mail is sent
            mass_mailing_ids = False
            if email == emails[-1]:
                mass_mailing_ids = self.ids

            # Used for Sendgrid -> Send e-mails in a job
            email.with_delay().send_sendgrid_job(mass_mailing_ids)

        emails.mapped('mailing_id').write({'state': 'sending'})
        return emails

    @api.multi
    def send_pending(self):
        """ Tries to send e-mails still pending. """
        self.ensure_one()
        mail_statistics = self.statistics_ids.filtered(
            lambda s: not s.mail_tracking_id and s.mail_mail_id.state ==
            'outgoing')
        emails = mail_statistics.mapped('mail_mail_id')
        emails.with_delay().send_sendgrid_job(self.ids)
        return True

    @api.multi
    def open_clicks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Click Events'),
            'view_type': 'form',
            'res_model': 'mail.tracking.event',
            'domain': [('id', 'in', self.mapped('click_event_ids').ids)],
            'view_mode': 'graph,tree,form',
            'target': 'current',
            'context': self.with_context(group_by='url').env.context
        }

    @api.multi
    def open_unsub(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unsubscribe Events'),
            'view_type': 'form',
            'res_model': 'mail.tracking.event',
            'domain': [('id', 'in', self.mapped('unsub_event_ids').ids)],
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context
        }

    @api.multi
    def open_emails(self):
        return self._open_tracking_emails([])

    @api.multi
    def open_received(self):
        return self._open_tracking_emails([
            ('state', 'in', ('delivered', 'opened'))])

    @api.multi
    def open_opened(self):
        return self._open_tracking_emails([
            ('state', '=', 'opened')
        ])

    def _open_tracking_emails(self, domain):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tracking Emails'),
            'view_type': 'form',
            'res_model': 'mail.tracking.email',
            'domain': [('mass_mailing_id', 'in', self.ids)] + domain,
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context
        }

    @api.model
    def _process_mass_mailing_queue(self):
        """
        Override cron to take only "in_queue" mass mailings.
        Pending mass_mailings may be still processing.
        :return: None
        """
        mass_mailings = self.search(
            [('state', '=', 'in_queue'), '|',
             ('schedule_date', '<', fields.Datetime.now()),
             ('schedule_date', '=', False)])
        for mass_mailing in mass_mailings:
            if len(mass_mailing.get_remaining_recipients()) > 0:
                mass_mailing.state = 'sending'
                mass_mailing.send_mail()
            else:
                mass_mailing.state = 'done'
