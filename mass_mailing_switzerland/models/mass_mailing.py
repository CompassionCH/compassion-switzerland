# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields, _

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession


class MassMailing(models.Model):
    """ Add the mailing domain to be viewed in a text field
    """
    _inherit = 'mail.mass_mailing'

    mailing_domain_copy = fields.Char(related='mailing_domain')
    click_ratio = fields.Integer(
        compute='compute_events', store=True)
    click_event_ids = fields.Many2many(
        'mail.tracking.event', compute='compute_events')
    unsub_ratio = fields.Integer(
        compute='compute_events', store=True)
    unsub_event_ids = fields.Many2many(
        'mail.tracking.event', compute='compute_events')

    @api.depends('statistics_ids', 'statistics_ids.tracking_event_ids')
    def compute_events(self):
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
            mass_mail.click_ratio = 100 * (
                float(number_click) / len(mass_mail.statistics_ids))
            mass_mail.unsub_ratio = 100 * (
                float(number_unsub) / len(mass_mail.statistics_ids))

    @api.multi
    def send_mail(self):
        result = super(MassMailing, self).send_mail()
        if self.email_template_id:
            # Used for Sendgrid -> Send e-mails in a job
            session = ConnectorSession.from_env(self.env)
            send_emails_job.delay(
                session, result._name, result.ids)
        return result

    @api.multi
    def send_pending(self):
        """ Tries to send e-mails still pending. """
        self.ensure_one()
        mail_statistics = self.statistics_ids.filtered(
            lambda s: not s.mail_tracking_id and s.mail_mail_id.state ==
            'outgoing')
        emails = mail_statistics.mapped('mail_mail_id')
        session = ConnectorSession.from_env(self.env)
        send_emails_job.delay(
            session, emails._name, emails.ids)
        return True

    @api.multi
    def open_clicks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Click Events'),
            'view_type': 'form',
            'res_model': 'mail.tracking.event',
            'domain': [('id', 'in', self.click_event_ids.ids)],
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
            'domain': [('id', 'in', self.unsub_event_ids.ids)],
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
            'domain': [('mass_mailing_id', '=', self.id)] + domain,
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context
        }


class MassMailingCampaign(models.Model):
    _inherit = 'mail.mass_mailing.campaign'

    click_ratio = fields.Integer(compute='_compute_ratios', store=True)
    unsub_ratio = fields.Integer(compute='_compute_ratios', store=True)

    @api.depends('mass_mailing_ids.click_ratio',
                 'mass_mailing_ids.unsub_ratio')
    def _compute_ratios(self):
        for campaign in self:
            total_clicks, total_unsub = 0
            total_sent = len(campaign.mapped(
                'mass_mailing_ids.statistics_ids'))
            for mailing in campaign.mass_mailing_ids:
                total_clicks += (mailing.click_ratio / 100.0) * len(
                    mailing.statistics_ids)
                total_unsub += (mailing.unsub_ratio / 100.0) * len(
                    mailing.statistics_ids)
            if total_sent:
                campaign.click_ratio = (total_clicks / total_sent) * 100
                campaign.unsub_ratio = (total_unsub / total_sent) * 100


##############################################################################
#                            CONNECTOR METHODS                               #
##############################################################################
def related_action_emails(session, job):
    email_ids = job.args[1]
    action = {
        'name': "E-mails",
        'type': 'ir.actions.act_window',
        'res_model': 'mail.mail',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'domain': [('id', 'in', email_ids)],
    }
    return action


@job(default_channel='root.mass_mailing')
@related_action(action=related_action_emails)
def send_emails_job(session, model_name, email_ids):
    """Job for sending e-mails with Sendgrid."""
    emails = session.env[model_name].browse(email_ids)
    emails.send_sendgrid()
