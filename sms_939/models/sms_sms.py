##############################################################################
#
#    Copyright (C) 2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class SmsSms(models.Model):
    _inherit = "sms.sms"

    error_detail = fields.Text(readonly=True)
    request_uid = fields.Text(readonly=True)

    def _split_batch(self):
        if self.env["sms.api"]._is_sent_with_mnc():
            # No batch with MNC - TODO
            for record in self:
                yield [record.id]
        else:
            yield from super()._split_batch()
