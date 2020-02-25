##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models
from odoo.addons.queue_job.job import job


class Hold(models.Model):
    _inherit = 'compassion.hold'

    @job(default_channel='root.global_pool')
    def update_expiration_date(self, new_date):
        self.write({
            'expiration_date': new_date
        })
