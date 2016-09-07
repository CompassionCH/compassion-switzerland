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

from openerp import api, models, fields

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession


class MassMailing(models.Model):
    """ Add the mailing domain to be viewed in a text field
    """
    _inherit = 'mail.mass_mailing'

    mailing_domain_copy = fields.Char(related='mailing_domain')

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
            lambda s: not s.tracking_state and s.mail_mail_id.state ==
            'outgoing')
        emails = mail_statistics.mapped('mail_mail_id')
        session = ConnectorSession.from_env(self.env)
        send_emails_job.delay(
            session, emails._name, emails.ids)
        return True


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
