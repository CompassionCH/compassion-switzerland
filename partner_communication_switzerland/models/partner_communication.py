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

from openerp import models, _


class PartnerCommunication(models.Model):
    _inherit = 'partner.communication.job'

    def get_dossier_full_attachments(self):
        return self._get_new_dossier_attachments()

    def get_dossier_payer_attachments(self):
        return self._get_new_dossier_attachments(correspondence=False)

    def get_dossier_correspondent_attachments(self):
        return self._get_new_dossier_attachments(payment=False)

    def get_correspondence_attachments(self):
        """
        Include PDF of letters only if less than 3 letters are sent,
        or if the send_mode is to print the letters.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        # Report is used for print configuration
        report = 'report_compassion.b2s_letter'
        letters = self.get_objects()
        if not letters.get_multi_mode() or self.send_mode == 'physical':
            for letter in self.get_objects():
                attachments[letter.letter_image.name] = \
                    [report, letter.letter_image.datas]
        else:
            # Attach directly a zip in the letters
            letters.attach_zip()
        return attachments

    def _get_new_dossier_attachments(self, correspondence=True, payment=True):
        """
        Returns pdfs for the New Dossier Communication, including:
        - Sponsorship payment slips (if payment is True)
        - Small Childpack
        - Sponsorship labels (if correspondence is True)
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        report_obj = self.env['report']

        sponsorship_ids = map(int, self.object_ids.split(','))
        sponsorships = self.env['recurring.contract'].browse(sponsorship_ids)
        if payment:
            report_name = 'report_compassion.3bvr_sponsorship'
            attachments.update({
                _('sponsorship payment slips.pdf'): [
                    report_name,
                    base64.b64encode(report_obj.get_pdf(
                        sponsorships, report_name,
                        data={'gifts': True, 'doc_ids': sponsorship_ids}
                    ))
                ]
            })

        children = sponsorships.mapped('child_id')
        report_name = 'report_compassion.childpack_small'
        attachments[_('child dossier.pdf')] = [
            report_name,
            base64.b64encode(report_obj.get_pdf(children, report_name))
        ]

        if correspondence:
            label_print = self.env['label.print'].search([
                ('name', '=', 'Sponsorship Label')], limit=1)
            label_brand = self.env['label.brand'].search([
                ('brand_name', '=', 'Herma A4')], limit=1)
            label_format = self.env['label.config'].search([
                ('name', '=', '4455 SuperPrint WeiB')], limit=1)
            label_wizard = self.env['label.print.wizard'].with_context({
                'active_ids': sponsorship_ids,
                'active_model': 'recurring.contract',
                'label_print': label_print.id,
            }).create({
                'brand_id': label_brand.id,
                'name': label_format.id,
                'number_of_labels': 33
            })
            label_data = label_wizard.get_report_data()
            label_context = self.env.context.copy()
            label_context.update(label_data['form'])
            label_context.update({
                'active_model': 'label.print.wizard',
                'active_id': label_wizard.id,
                'active_ids': label_wizard.ids,
                'label_print': label_print.id
            })
            report_name = 'label.report_label'
            attachments[_('sponsorship labels.pdf')] = [
                report_name,
                base64.b64encode(
                    report_obj.with_context(label_context).get_pdf(
                        label_wizard, report_name, data=label_data))
            ]

        return attachments
