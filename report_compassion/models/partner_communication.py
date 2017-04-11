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
import base64
from datetime import datetime

from contract_group import setlocale
from res_partner import IMG_DIR

from openerp import api, models, fields


class PartnerCommunication(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'partner.communication.job'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    date_communication = fields.Char(compute='_compute_date_communication')
    signature = fields.Char(compute='_compute_signature')
    success_story_id = fields.Many2one('success.story', 'Success Story')
    print_subject = fields.Boolean(default=True)
    product_id = fields.Many2one('product.product', 'Attach payment slip for')
    compassion_logo = fields.Binary(compute='_compute_compassion_logo')
    compassion_square = fields.Binary(compute='_compute_compassion_logo')
    print_header = fields.Boolean()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
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
            signature += user.company_id.name.split(' ')[0] + ' '
            signature += user.company_id.country_id.name
            communication.signature = signature

    @api.multi
    def _compute_compassion_logo(self):
        with open(IMG_DIR + '/compassion_logo.png') as logo:
            with open(IMG_DIR + '/bluesquare.png') as square:
                data_logo = base64.b64encode(logo.read())
                data_square = base64.b64encode(square.read())
                for communication in self:
                    communication.compassion_logo = data_logo
                    communication.compassion_square = data_square

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def set_success_story(self):
        """
        Takes the less used active success story and attach it
        to communications.
        :return: True
        """
        for job in self:
            story = self.env['success.story'].search([
                ('is_active', '=', True)]).sorted(
                lambda s: s.current_usage_count)
            if story:
                if len(story) == 1:
                    job.success_story_id = story
                else:
                    usage_count = dict()
                    for s in reversed(story):
                        usage = self.search_count([
                            ('partner_id', '=', job.partner_id.id),
                            ('success_story_id', '=', s.id)
                        ])
                        usage_count[usage] = s
                    min_used = min(usage_count.keys())
                    job.success_story_id = usage_count[min_used]

        return True

    @api.multi
    def refresh_text(self, refresh_uid=False):
        """
        Refresh the success story as well
        :param refresh_uid: User that refresh
        :return: True
        """
        super(PartnerCommunication, self).refresh_text(refresh_uid)
        self.filtered('success_story_id').set_success_story()
        return True

    @api.multi
    def send(self):
        """
        Change the report for communications to print with BVR
        Update the count of succes story prints when sending a receipt.
        :return: True
        """
        print_bvr = self.filtered(lambda j: j.send_mode == 'physical' and
                                  j.product_id)
        print_bvr.write({'report_id': self.env.ref(
            'report_compassion.report_a4_bvr').id})
        res = super(PartnerCommunication, self).send()
        for job in self.filtered('success_story_id').filtered('sent_date'):
            job.success_story_id.print_count += 1

        return res


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # Translate name of department for signatures
    name = fields.Char(translate=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Translate name of Company for signatures
    address_name = fields.Char(translate=True)
