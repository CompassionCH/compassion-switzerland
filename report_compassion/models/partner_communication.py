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
from datetime import datetime

from openerp import api, models, fields


class PartnerCommunication(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'partner.communication.job'

    date_communication = fields.Char(compute='_compute_date_communication')
    signature = fields.Char(compute='_compute_signature')

    @api.multi
    def _compute_date_communication(self):
        lang_map = {
            'fr_CH': 'le %d %B %Y',
            'de_DE': '%d. %B %Y',
            'en_US': '%d %B %Y',
            'it_IT': '%d %B %Y',
        }
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for communication in self:
            communication.date_communication = city + ", " + today.strftime(
                lang_map.get(self.env.lang))

    @api.multi
    def _compute_signature(self):
        for communication in self:
            user = self.user_id or self.env.user
            employee = user.employee_ids
            signature = ''
            if len(employee) == 1:
                signature = employee.name + '<br/>' + \
                            employee.department_id.name + '<br/>'
            signature += self.env.user.company_id.name
            communication.signature = signature


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # Translate name of department for signatures
    name = fields.Char(translate=True)
