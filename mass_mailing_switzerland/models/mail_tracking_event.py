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

from openerp import models, api

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession


class MailTrackingEvent(models.Model):
    _inherit = "mail.tracking.event"

    @api.model
    def process_click(self, tracking_email, metadata):
        """ Update mass mailing stats. """
        mass_mail = tracking_email.mass_mailing_id
        if mass_mail:
            session = ConnectorSession.from_env(self.env)
            update_mass_mail_stats.delay(
                session, mass_mail._name, mass_mail.id)
        return super(MailTrackingEvent, self).process_click(
            tracking_email, metadata)


@job(default_channel='root.mass_mailing_switzerland')
def update_mass_mail_stats(session, model_name, mass_mail_id):
    """Job for updating mass mailing click statistics."""
    session.env[model_name].browse(mass_mail_id).compute_click_events()
