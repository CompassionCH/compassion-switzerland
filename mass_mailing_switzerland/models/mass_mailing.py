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


class MassMailing(models.Model):
    """ Add the mailing domain to be viewed in a text field
    """
    _inherit = 'mail.mass_mailing'

    internal_name = fields.Char("Internal Variant Name")
    total = fields.Integer(compute="_compute_statistics")

    mailing_domain_copy = fields.Char(related='mailing_domain')
    clicks_ratio = fields.Integer(compute=False)
    click_event_ids = fields.Many2many(
        'mail.tracking.event', compute='_compute_events')
    unsub_ratio = fields.Integer()
    unsub_event_ids = fields.Many2many(
        'mail.tracking.event', compute='_compute_events')
    partner_test_sendgrid_id = fields.Many2one('res.partner',
                                               'Test Partner')

    @api.multi
    def name_get(self):
        res = []
        for mass_mail in self:
            _id, _name = super(MassMailing, mass_mail).name_get()[0]
            if mass_mail.internal_name:
                res.append((_id, f"{_name} [{mass_mail.internal_name}]"))
            else:
                res.append((_id, _name))
        return res

    def compute_clicks_ratio(self):
        for mass_mail in self.filtered('statistics_ids.tracking_event_ids'):
            clicks = self.env['mail.mail.statistics'].search_count([
                ('tracking_event_ids.event_type', '=', 'click'),
                ('mass_mailing_id', '=', mass_mail.id)
            ])
            mass_mail.clicks_ratio = 100 * (
                float(clicks) / len(mass_mail.statistics_ids))

    def compute_unsub_ratio(self):
        for mass_mail in self.filtered('statistics_ids.tracking_event_ids'):
            unsub = self.env['mail.mail.statistics'].search_count([
                ('tracking_event_ids.event_type', '=', 'unsub'),
                ('mass_mailing_id', '=', mass_mail.id)
            ])
            mass_mail.unsub_ratio = 100 * (
                float(unsub) / len(mass_mail.statistics_ids))

    def recompute_states(self):
        self.env['mail.mail.statistics'].search([
            ('mass_mailing_id', 'in', self.ids)])._compute_state()

        self._compute_statistics()

    def _compute_statistics(self):
        self.env.cr.execute("""
            SELECT
                m.id as mailing_id,
                COUNT(CASE WHEN s.state != 'outgoing'
                    THEN 1 ELSE null END) AS sent,
                COUNT(CASE WHEN s.state = 'outgoing'
                    THEN 1 ELSE null END) AS scheduled,
                COUNT(CASE WHEN t.state = 'rejected'
                    THEN 1 ELSE null END) AS failed,
                COUNT(CASE WHEN t.state = 'delivered' OR
                    t.state = 'opened'
                    THEN 1 ELSE null END) AS delivered,
                COUNT(CASE WHEN t.state = 'opened'
                    THEN 1 ELSE null END) AS opened,
                COUNT(CASE WHEN s.replied is not null
                    THEN 1 ELSE null END) AS replied,
                COUNT(CASE WHEN t.state = 'bounced' OR
                    t.state = 'spam'
                    THEN 1 ELSE null END) AS bounced
            FROM
                mail_tracking_email t
            RIGHT JOIN
                mail_mass_mailing m
                ON (m.id = t.mass_mailing_id)
            RIGHT JOIN
                mail_mail_statistics s
                ON (m.id = s.mass_mailing_id AND t.mail_stats_id = s.id)
            WHERE
                m.id IN %s
            GROUP BY m.id
        """, (tuple(self.ids), ))

        for row in self.env.cr.dictfetchall():
            row['total'] = row['sent']
            row['received_ratio'] = 100.0 * row['delivered'] / row['total']
            row['opened_ratio'] = 100.0 * row['opened'] / row['total']
            row['replied_ratio'] = 100.0 * row['replied'] / row['total']
            row['bounced_ratio'] = 100.0 * row['bounced'] / row['total']
            self.browse(row.pop('mailing_id')).update(row)

    def _compute_events(self):
        for mass_mail in self:
            unsub = self.env['mail.tracking.event'].search([
                ('event_type', '=', 'unsub'),
                ('mass_mailing_id', '=', mass_mail.id)
            ])
            clicks = self.env['mail.tracking.event'].search([
                ('event_type', '=', 'click'),
                ('mass_mailing_id', '=', mass_mail.id)
            ])
            mass_mail.click_event_ids = clicks
            mass_mail.unsub_event_ids = unsub

    @api.depends('email_template_id', 'partner_test_sendgrid_id')
    def _compute_sendgrid_view(self):
        # change all substitutions if the test partner is set
        for wizard in self:
            res_id = wizard.partner_test_sendgrid_id.id
            template = wizard.email_template_id.with_context(
                lang=wizard.partner_test_sendgrid_id.lang or
                self.env.context['lang'])
            sendgrid_template = template.sendgrid_localized_template
            if sendgrid_template and res_id:
                render_body = template.render_template(
                    template.body_html, template.model, [res_id],
                    post_process=True)[res_id]
                body_sendgrid = sendgrid_template.html_content.replace(
                    '<%body%>', render_body)
                substitutions = template.render_substitutions(res_id)
                for sub in substitutions[res_id]:
                    key = sub[2]['key']
                    value = sub[2]['value']
                    res_value = template.render_template(
                        value, template.model, [res_id]
                    )[res_id]
                    body_sendgrid = body_sendgrid.replace(key, res_value)
                wizard.body_sendgrid = body_sendgrid
            else:
                super(MassMailing, wizard)._compute_sendgrid_view()

    @api.onchange('partner_test_sendgrid_id')
    def compute_sendgrid_view_test(self):
        self.with_context(
            {'lang': self.lang.code or
             self.partner_test_sendgrid_id.lang}
        )._compute_sendgrid_view()

    @api.multi
    def recompute_events(self):
        self.recompute_states()
        self.compute_unsub_ratio()
        self.compute_clicks_ratio()
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
        for mailing in self.with_context(must_skip_send_to_printer=True):
            substitutions = mailing.mapped(
                'email_template_id.substitution_ids')
            substitutions.replace_tracking_link(
                campaign_id=mailing.mass_mailing_campaign_id.campaign_id.id,
                medium_id=mass_mailing_medium_id,
                source_id=mailing.source_id.id
            )
            emails += super(MassMailing, mailing).send_mail()

        emails_list = []
        final_state = 'sending'
        duplicate_emails = self.env['mail.mail']

        for email in emails:
            # Only update mass mailing state when last e-mail is sent
            mass_mailing_ids = False
            if email == emails[-1]:
                mass_mailing_ids = self.ids

            recipients = [email.email_to] if email.email_to else []
            recipients.extend(email.recipient_ids.mapped('email'))
            if not all(recipient in emails_list for recipient in recipients):
                emails_list.extend(recipients)
                # Used for Sendgrid -> Send e-mails in a job
                email.with_delay().send_sendgrid_job(mass_mailing_ids)
            else:
                # Remove the e-mail, as the recipients already received it.
                statistics = self.env['mail.mail.statistics'].search([(
                    'mail_mail_id', '=', email.id
                )])
                statistics.unlink()
                duplicate_emails += email
                if email == emails[-1]:
                    # Force the final state to done as it won't be updated by
                    # sending jobs
                    final_state = 'done'

        duplicate_emails.unlink()
        self.write({'state': final_state})
        return emails - duplicate_emails

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
            'domain': [('mass_mailing_id', 'in', self.ids),
                       ('mail_stats_id', '!=', None)] + domain,
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
