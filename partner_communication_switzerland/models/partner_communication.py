# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import time
import logging
import re

from ..wizards.generate_communication_wizard import SMS_CHAR_LIMIT, SMS_COST
from math import ceil
from collections import OrderedDict
from datetime import date, datetime
from io import BytesIO

from dateutil.relativedelta import relativedelta
from odoo.addons.sponsorship_compassion.models.product import GIFT_NAMES

from odoo import api, models, _, fields
from odoo.exceptions import MissingError, UserError

_logger = logging.getLogger(__name__)

try:
    from pyPdf import PdfFileWriter, PdfFileReader
    from bs4 import BeautifulSoup
except ImportError:
    _logger.warning("Please install pypdf and bs4 for using the module")


class PartnerCommunication(models.Model):
    _inherit = 'partner.communication.job'

    event_id = fields.Many2one('crm.event.compassion', 'Event')
    ambassador_id = fields.Many2one('res.partner', 'Ambassador')
    currency_id = fields.Many2one('res.currency', compute='_compute_currency')
    utm_campaign_id = fields.Many2one('utm.campaign')
    sms_cost = fields.Float()
    sms_provider_id = fields.Many2one(
        'sms.provider', 'SMS Provider',
        default=lambda self: self.env.ref('sms_939.large_account_id', False),
        readonly=False)

    @api.model
    def send_mode_select(self):
        modes = super(PartnerCommunication, self).send_mode_select()
        modes.append(('sms', _('SMS')))
        return modes

    @api.multi
    def _compute_currency(self):
        chf = self.env.ref('base.CHF')
        for wizard in self:
            wizard.currency_id = chf.id

    def get_correspondence_attachments(self):
        """
        Include PDF of letters if the send_mode is to print the letters.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        # Report is used for print configuration
        report = 'report_compassion.b2s_letter'
        letters = self.get_objects()
        if self.send_mode == 'physical':
            for letter in self.get_objects():
                try:
                    attachments[letter.file_name] = [
                        report, self._convert_pdf(letter.letter_image)]
                except MissingError:
                    _logger.warn("Missing letter image", exc_info=True)
                    self.send_mode = False
                    self.auto_send = False
                    self.message_post(
                        _('The letter image is missing!'), _("Missing letter"))
                    continue
        else:
            # Attach directly a zip in the letters
            letters.attach_zip()
        return attachments

    def get_birthday_bvr(self):
        """
        Attach birthday gift slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        background = self.send_mode and 'physical' not in self.send_mode
        sponsorships = self.get_objects().filtered(
            lambda s: not s.birthday_paid)
        gifts_to = sponsorships[:1].gift_partner_id
        if sponsorships and gifts_to == self.partner_id:
            birthday_gift = self.env['product.product'].with_context(
                lang='en_US').search([('name', '=', GIFT_NAMES[0])])
            attachments = sponsorships.get_bvr_gift_attachment(
                birthday_gift, background)
        return attachments

    def get_graduation_bvr(self):
        """
        Attach graduation gift slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        background = self.send_mode and 'physical' not in self.send_mode
        sponsorships = self.get_objects()
        graduation = self.env['product.product'].with_context(
            lang='en_US').search([('name', '=', GIFT_NAMES[4])])
        gifts_to = sponsorships[0].gift_partner_id
        if sponsorships and gifts_to == self.partner_id:
            attachments = sponsorships.get_bvr_gift_attachment(
                graduation, background)
        return attachments

    def get_reminder_bvr(self):
        """
        Attach sponsorship due payment slip with background for sending by
        e-mail.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()

        # Verify big due periods
        if len(sponsorships.mapped('months_due')) > 3:
            self.need_call = 'before_sending'

        payment_mode = sponsorships.with_context(lang='en_US').mapped(
            'payment_mode_id.name')[0]
        # LSV-DD Waiting reminders special case
        if 'Waiting Reminder' in self.config_id.name and (
                'LSV' in payment_mode or 'Postfinance' in payment_mode):
            if self.partner_id.bank_ids:
                # We received the bank info but withdrawal didn't work.
                # Mark to call in order to verify the situation.
                self.need_call = 'before_sending'
            else:
                # Don't put payment slip if we just wait the authorization form
                return dict()

        # Put product sponsorship to print the payment slip for physical print.
        if self.send_mode and 'physical' in self.send_mode:
            self.product_id = self.env[
                'product.product'].with_context(lang='en_US').search([
                    ('name', '=', 'Sponsorship')], limit=1)
            return dict()

        # In other cases, attach the payment slip.
        report_name = 'report_compassion.bvr_due'
        return {
            _('sponsorship due.pdf'): [
                report_name,
                base64.b64encode(self.env['report'].get_pdf(
                    sponsorships.ids, report_name,
                    data={'background': True, 'doc_ids': sponsorships.ids}
                ))
            ]
        }

    def get_label_from_sponsorship(self):
        """
        Attach sponsorship labels. Used from communication linked to children.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()
        return self.get_label_attachment(sponsorships)

    def get_label_attachment(self, sponsorships=False):
        """
        Attach sponsorship labels. Used from communication linked to children.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        if not sponsorships:
            sponsorships = self.env['recurring.contract']
            children = self.get_objects()
            for child in children:
                sponsorships += child.sponsorship_ids[0]
        attachments = dict()
        label_print = self.env['label.print'].search([
            ('name', '=', 'Sponsorship Label')], limit=1)
        label_brand = self.env['label.brand'].search([
            ('brand_name', '=', 'Herma A4')], limit=1)
        label_format = self.env['label.config'].search([
            ('name', '=', '4455 SuperPrint WeiB')], limit=1)
        label_wizard = self.env['label.print.wizard'].with_context({
            'active_ids': sponsorships.ids,
            'active_model': 'recurring.contract',
            'label_print': label_print.id,
            'must_skip_send_to_printer': True
        }).create({
            'brand_id': label_brand.id,
            'config_id': label_format.id,
            'number_of_labels': 33
        })
        label_data = label_wizard.get_report_data()
        report_name = 'label.report_label'
        attachments[_('sponsorship labels.pdf')] = [
            report_name,
            base64.b64encode(
                label_wizard.env['report'].get_pdf(
                    label_wizard.ids, report_name, data=label_data))
        ]
        return attachments

    def get_child_picture_attachment(self):
        """
        Attach child pictures to communication. It directly attach them
        to the communication if sent by e-mail and therefore does
        return an empty dictionary.
        :return: dict {}
        """
        self.ensure_one()
        res = dict()
        if self.send_mode and 'physical' not in self.send_mode:
            # Prepare attachments in case the communication is sent by e-mail
            children = self.get_objects()
            attachments = self.env['ir.attachment']
            for child in children:
                pic = child.pictures_ids[0]
                attachment = self.env['ir.attachment'].search([
                    ('res_model', '=', 'compassion.child.pictures'),
                    ('res_id', '=', pic.id),
                    ('datas_fname', 'like', 'Fullshot')
                ], limit=1)
                attachments += attachment.copy({
                    'name': child.local_id + ' ' + child.last_photo_date +
                    '.jpg',
                    'res_model': self._name,
                    'res_id': self.id
                })
            self.with_context(no_print=True).ir_attachment_ids = attachments
        else:
            self.ir_attachment_ids = False
        return res

    def get_yearly_payment_slips(self):
        """
        Attach payment slips
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()
        payment_mode_bvr = self.env.ref(
            'sponsorship_switzerland.payment_mode_bvr')
        attachments = dict()
        # IF payment mode is BVR and partner is paying
        # attach sponsorship payment slips
        pay_bvr = sponsorships.filtered(
            lambda s: s.payment_mode_id == payment_mode_bvr and
            s.partner_id == self.partner_id)
        report_obj = self.env['report']
        if pay_bvr and pay_bvr.must_pay_next_year():
            today = date.today()
            date_start = today.replace(today.year + 1, 1, 1)
            date_stop = date_start.replace(month=12, day=31)
            report_name = 'report_compassion.3bvr_sponsorship'
            attachments.update({
                _('sponsorship payment slips.pdf'): [
                    report_name,
                    base64.b64encode(report_obj.get_pdf(
                        pay_bvr.ids, report_name,
                        data={
                            'doc_ids': pay_bvr.ids,
                            'date_start': fields.Date.to_string(date_start),
                            'date_stop': fields.Date.to_string(date_stop),
                            'background': self.send_mode != 'physical'
                        }
                    ))
                ]
            })
        # Attach gifts for correspondents
        pays_gift = self.env['recurring.contract']
        for sponsorship in sponsorships:
            if sponsorship.mapped(sponsorship.send_gifts_to) == \
                    self.partner_id:
                pays_gift += sponsorship
        if pays_gift:
            report_name = 'report_compassion.3bvr_gift_sponsorship'
            attachments.update({
                _('sponsorship gifts.pdf'): [
                    report_name,
                    base64.b64encode(report_obj.get_pdf(
                        pays_gift.ids, report_name,
                        data={'doc_ids': pays_gift.ids}
                    ))
                ]
            })
        return attachments

    def get_childpack_attachment(self):
        self.ensure_one()
        lang = self.partner_id.lang
        sponsorships = self.get_objects()
        exit_conf = self.env.ref(
            'partner_communication_switzerland.lifecycle_child_planned_exit')
        if self.config_id == exit_conf and sponsorships.mapped(
                'sub_sponsorship_id'):
            sponsorships = sponsorships.mapped('sub_sponsorship_id')
        children = sponsorships.mapped('child_id')
        # Always retrieve latest information before printing dossier
        children.get_infos()
        report_name = 'report_compassion.childpack_small'
        return {
            _('child dossier.pdf'): [
                report_name,
                base64.b64encode(self.env['report'].get_pdf(
                    children.ids, report_name, data={
                        'lang': lang,
                        'is_pdf': self.send_mode != 'physical',
                        'type': report_name,
                    }))
            ]
        }

    def get_tax_receipt(self):
        self.ensure_one()
        res = {}
        if self.send_mode == 'digital':
            report_name = 'report_compassion.tax_receipt'
            data = {
                'doc_ids': self.partner_id.ids,
                'year': self.env.context.get('year', date.today().year - 1),
                'lang': self.partner_id.lang,
            }
            res = {
                _('tax receipt.pdf'): [
                    report_name,
                    base64.b64encode(
                        self.env['report'].with_context(
                            must_skip_send_to_printer=True).get_pdf(
                            self.partner_id.ids, report_name, data=data))
                ]
            }
        return res

    @api.multi
    def send(self):
        """
        - Prevent sending communication when invoices are being reconciled
        - Mark B2S correspondence as read when printed.
        - Postpone no money holds when reminders sent.
        - Update donor tag
        - Sends SMS for sms send_mode
        :return: True
        """
        sms_jobs = self.filtered(lambda j: j.send_mode == 'sms')
        sms_jobs.send_by_sms()
        other_jobs = self - sms_jobs
        for job in other_jobs.filtered(lambda j: j.model in (
                'recurring.contract', 'account.invoice')):
            queue_job = self.env['queue.job'].search([
                ('channel', '=', 'root.group_reconcile'),
                ('state', '!=', 'done'),
            ], limit=1)
            if queue_job:
                invoices = self.env['account.invoice'].browse(
                    queue_job.record_ids)
                if job.partner_id in invoices.mapped('partner_id'):
                    retry = 0
                    state = queue_job.state
                    while state != 'done' and retry < 5:
                        if queue_job.state == 'failed':
                            raise UserError(_(
                                "A reconcile job has failed. Please call "
                                "an admin for help."
                            ))
                        _logger.info("Reconcile job is processing! Going in "
                                     "sleep for five seconds...")
                        time.sleep(5)
                        state = queue_job.read(['state'])[0]['state']
                        retry += 1
                    if queue_job.state != 'done':
                        raise UserError(_(
                            "Some invoices of the partner are just being "
                            "reconciled now. Please wait the process to finish"
                            " before printing the communication."
                        ))
        super(PartnerCommunication, other_jobs).send()
        b2s_printed = other_jobs.filtered(
            lambda c: c.config_id.model == 'correspondence' and
            c.send_mode == 'physical' and c.state == 'done')
        if b2s_printed:
            letters = b2s_printed.get_objects()
            if letters:
                letters.write({
                    'letter_delivered': True,
                })

        # No money extension
        no_money_1 = self.env.ref('partner_communication_switzerland.'
                                  'sponsorship_waiting_reminder_1')
        no_money_2 = self.env.ref('partner_communication_switzerland.'
                                  'sponsorship_waiting_reminder_2')
        no_money_3 = self.env.ref('partner_communication_switzerland.'
                                  'sponsorship_waiting_reminder_3')
        settings = self.env['availability.management.settings']
        first_extension = settings.get_param('no_money_hold_duration')
        second_extension = settings.get_param('no_money_hold_extension')
        for communication in other_jobs:
            extension = False
            if communication.config_id == no_money_1:
                extension = first_extension + 7
            elif communication.config_id == no_money_2:
                extension = second_extension + 7
            elif communication.config_id == no_money_3:
                extension = 10
            if extension:
                holds = communication.get_objects().mapped('child_id.hold_id')
                for hold in holds:
                    expiration = datetime.now() + relativedelta(days=extension)
                    hold.expiration_date = fields.Datetime.to_string(
                        expiration)

        donor = self.env.ref('partner_compassion.res_partner_category_donor')
        partners = other_jobs.filtered(
            lambda j: j.config_id.model == 'account.invoice.line' and
            donor not in j.partner_id.category_id).mapped('partner_id')
        partners.write({'category_id': [(4, donor.id)]})

        return True

    @api.multi
    def send_by_sms(self):
        """
        Sends communication jobs with SMS 939 service.
        :return: list of sms_texts
        """
        link_pattern = re.compile(r'<a href="(.*)">(.*)</a>', re.DOTALL)
        sms_medium_id = self.env.ref('sms_sponsorship.utm_medium_sms').id
        sms_texts = []
        for job in self.filtered('partner_mobile'):
            sms_text = job.convert_html_for_sms(link_pattern, sms_medium_id)
            sms_texts.append(sms_text)
            sms_wizard = self.env['sms.sender.wizard'].with_context(
                partner_id=job.partner_id.id).create({
                    'subject': job.subject,
                    'text': sms_text,
                    'sms_provider_id': job.sms_provider_id.id
                })
            sms_wizard.send_sms_partner()
            job.write({
                'state': 'done',
                'sent_date': fields.Datetime.now(),
                'sms_cost': ceil(
                    float(len(sms_text)) / SMS_CHAR_LIMIT) * SMS_COST
            })
        return sms_texts

    def convert_html_for_sms(self, link_pattern, sms_medium_id):
        """
        Converts HTML into simple text for SMS.
        First replace links with short links using Link Tracker.
        Then clean HTML using BeautifulSoup library.
        :param link_pattern: the regex pattern for replacing links
        :param sms_medium_id: the associated utm.medium id for generated links
        :return: Clean text with short links for SMS use.
        """
        self.ensure_one()
        source_id = self.config_id.source_id.id

        def _replace_link(match):

            full_link = match.group(1).replace('&amp;', '&')
            short_link = self.env['link.tracker'].create({
                'url': full_link,
                'campaign_id': self.utm_campaign_id.id or self.env.ref(
                    'partner_communication_switzerland.'
                    'utm_campaign_communication').id,
                'medium_id': sms_medium_id,
                'source_id': source_id
            })
            return short_link.short_url

        links_converted_text = link_pattern.sub(_replace_link, self.body_html)
        soup = BeautifulSoup(links_converted_text, "lxml")
        return soup.get_text().strip()

    @api.multi
    def open_related(self):
        """ Select a better view for invoice lines. """
        res = super(PartnerCommunication, self).open_related()
        if self.config_id.model == 'account.invoice.line':
            res['context'] = self.with_context(
                tree_view_ref='sponsorship_compassion'
                              '.view_invoice_line_partner_tree',
                group_by=False
            ).env.context
        return res

    def get_new_dossier_attachments(self):
        """
        Returns pdfs for the New Dossier Communication, including:
        - Sponsorship payment slips (if payment is True)
        - Small Childpack
        - Sponsorship labels (if correspondence is True)
        - Child picture
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = OrderedDict()
        report_obj = self.env['report']
        account_payment_mode_obj = self.env['account.payment.mode']
        sponsorships = self.get_objects()

        # Include all active sponsorships for Permanent Order
        if 'Permanent Order' in sponsorships.with_context(
                lang='en_US').mapped('payment_mode_id.name'):
            sponsorships += sponsorships.mapped(
                'group_id.contract_ids').filtered(
                lambda s: s.state == 'active')

        is_payer = self.partner_id in sponsorships.mapped('partner_id')
        correspondence = self.partner_id in sponsorships.mapped(
            'correspondent_id')
        make_payment_pdf = True

        # LSV/DD don't need a payment slip
        groups = sponsorships.mapped('group_id')
        lsv_dd_modes = account_payment_mode_obj.search(
            ['|', ('name', 'like', 'Direct Debit'), ('name', 'like', 'LSV')])
        lsv_dd_groups = groups.filtered(
            lambda r: r.payment_mode_id in lsv_dd_modes)
        if len(lsv_dd_groups) == len(groups):
            make_payment_pdf = False

        # If sponsor already paid, avoid payment slip
        if len(sponsorships.filtered('period_paid')) == len(sponsorships):
            make_payment_pdf = False

        # Payment slips
        if is_payer and make_payment_pdf:
            report_name = 'report_compassion.3bvr_sponsorship'
            attachments.update({
                _('sponsorship payment slips.pdf'): [
                    report_name,
                    base64.b64encode(report_obj.get_pdf(
                        sponsorships.ids, report_name,
                        data={
                            'doc_ids': sponsorships.ids,
                            'background': self.send_mode != 'physical'
                        }
                    ))
                ]
            })

        # Gifts
        sponsorships = self.get_objects()
        gifts_sponsorship = sponsorships.filtered(
            lambda s: s.gift_partner_id == self.partner_id
            and s.type == 'S'
        )
        report_name = 'report_compassion.3bvr_gift_sponsorship'
        if gifts_sponsorship:
            attachments.update({
                _('sponsorship gifts.pdf'): [
                    report_name,
                    base64.b64encode(report_obj.get_pdf(
                        gifts_sponsorship.ids, report_name,
                        data={
                            'doc_ids': gifts_sponsorship.ids,
                            'background': self.send_mode != 'physical'
                        }
                    ))
                ]
            })

        # Childpack if not a SUB of planned exit.
        lifecycle = sponsorships.mapped('parent_id.child_id.lifecycle_ids')
        planned_exit = lifecycle and lifecycle[0].type == 'Planned Exit'
        if not planned_exit:
            attachments.update(self.get_childpack_attachment())

        # Labels
        if correspondence:
            attachments.update(self.get_label_attachment(sponsorships))

        # Child picture
        report_name = 'partner_communication_switzerland.child_picture'
        child_ids = sponsorships.mapped('child_id').ids
        attachments.update({
            _('child picture.pdf'): [
                report_name,
                base64.b64encode(report_obj.get_pdf(
                    child_ids, report_name,
                    data={'doc_ids': child_ids}
                ))
            ]
        })

        return attachments

    def get_csp_attachment(self):
        self.ensure_one()
        attachments = OrderedDict()
        report_obj = self.env['report']
        account_payment_mode_obj = self.env['account.payment.mode']
        csp = self.get_objects()

        # Include all active csp for Permanent Order
        if 'Permanent Order' in csp.with_context(
                lang='en_US').mapped('payment_mode_id.name'):
            csp += csp.mapped(
                'group_id.contract_ids').filtered(
                lambda s: s.state == 'active')

        is_payer = self.partner_id in csp.mapped('partner_id')
        make_payment_pdf = True

        # LSV/DD don't need a payment slip
        groups = csp.mapped('group_id')
        lsv_dd_modes = account_payment_mode_obj.search(
            ['|', ('name', 'like', 'Direct Debit'), ('name', 'like', 'LSV')])
        lsv_dd_groups = groups.filtered(
            lambda r: r.payment_mode_id in lsv_dd_modes)
        if len(lsv_dd_groups) == len(groups):
            make_payment_pdf = False

        # If partner already paid, avoid payment slip
        if len(csp.filtered('period_paid')) == len(csp):
            make_payment_pdf = False

        # Payment slips
        if is_payer and make_payment_pdf:
            report_name = 'report_compassion.3bvr_sponsorship'
            attachments.update({
                _('csv payment slips.pdf'): [
                    report_name,
                    base64.b64encode(report_obj.get_pdf(
                        csp.ids, report_name,
                        data={
                            'doc_ids': csp.ids,
                            'background': self.send_mode != 'physical'
                        }
                    ))
                ]
            })

        return attachments

    def _convert_pdf(self, pdf_data):
        """
        Converts all pages of PDF in A4 format if communication is
        printed.
        :param pdf_data: binary data of original pdf
        :return: binary data of converted pdf
        """
        if self.send_mode != 'physical':
            return pdf_data

        pdf = PdfFileReader(BytesIO(base64.b64decode(pdf_data)))
        convert = PdfFileWriter()
        a4_width = 594.48
        a4_height = 844.32  # A4 units in PyPDF
        for i in xrange(0, pdf.numPages):
            # translation coordinates
            tx = 0
            ty = 0
            page = pdf.getPage(i)
            corner = [float(x) for x in page.mediaBox.getUpperRight()]
            if corner[0] > a4_width or corner[1] > a4_height:
                page.scaleBy(max(a4_width / corner[0], a4_height / corner[1]))
            elif corner[0] < a4_width or corner[1] < a4_height:
                tx = (a4_width - corner[0]) / 2
                ty = (a4_height - corner[1]) / 2
            convert.addBlankPage(a4_width, a4_height)
            convert.getPage(i).mergeTranslatedPage(page, tx, ty)
        output_stream = BytesIO()
        convert.write(output_stream)
        output_stream.seek(0)
        return base64.b64encode(output_stream.read())
