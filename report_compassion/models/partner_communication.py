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

from contract_group import setlocale
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
            'fr_CH': u'le %d %B %Y',
            'de_DE': u'%d. %B %Y',
            'en_US': u'%d %B %Y',
            'it_IT': u'%d %B %Y',
        }
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for communication in self:
            lang = communication.partner_id.lang
            with setlocale(lang):
                date = today.strftime(lang_map.get(lang)).decode('utf-8')
                communication.date_communication = city + u", " + date

    @api.multi
    def _compute_signature(self):
        for communication in self:
            user = communication.user_id or self.env.user
            user = user.with_context(lang=communication.partner_id.lang)
            employee = user.employee_ids
            signature = ''
            if len(employee) == 1:
                signature = employee.name + '<br/>' + \
                            employee.department_id.name + '<br/>'
            signature += user.company_id.name
            communication.signature = signature


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # Translate name of department for signatures
    name = fields.Char(translate=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Translate name of Company for signatures
    address_name = fields.Char(translate=True)
