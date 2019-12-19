# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier, Loic Hausammann, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import logging
import time
import urllib2
import base64
from io import BytesIO

from odoo.addons.sbc_compassion.tools import import_letter_functions as func
from odoo.addons.sbc_switzerland.models.import_letters_history import SmbConfig

from odoo import models, api, fields

logger = logging.getLogger(__name__)


class ImportLetterLine(models.Model):
    _inherit = 'import.letter.line'

    email = fields.Char(help='Origin e-mail of submission', readonly=True)
    partner_name = fields.Char(help='Origin name of submission', readonly=True)


class ImportLetterReview(models.TransientModel):
    _inherit = 'import.letters.review'

    email = fields.Char(related='current_line_id.email')
    partner_name = fields.Char(related='current_line_id.partner_name')


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class add to its parent the possibility to select letters to import
    from a specify config.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """
    _inherit = 'import.letters.history'

    @api.model
    def import_web_letter(self, child_code, sponsor_ref, name, email,
                          original_text, template_name, pdf_url,
                          attachment_url, ext, utm_source, utm_medium,
                          utm_campaign):
        """
        Called when a letter is sent from the Wordpress web site:
            - add the letter into an import set with import letter config 'Web letter'
        """
        logger.info("New webletter from Wordpress : %s - %s",
                    sponsor_ref, child_code)
        try:
            # Find existing config or create a new one
            web_letter_id = self.env.ref('sbc_switzerland.web_letter').id
            import_config = self.search([
                ('config_id', '=', web_letter_id),
                ('state', '!=', 'done')], limit=1)
            if not import_config:
                import_config = self.create({
                    'config_id': web_letter_id, 'state': 'open'})

            # Retrieve child id
            child_id = func.find_child(self.env, child_code)

            # Retrieve sponsor id
            sponsor_id = func.find_partner(self.env, sponsor_ref, email)

            # Detect original language of the text
            lang = self.env['correspondence'].detect_lang(original_text)
            lang_id = lang and lang.id

            # Retrieve the template given its name
            template = self.env['correspondence.template'].search(
                [('name', '=', template_name)], limit=1)

            # Retrieve the PDF generated and hosted by WP
            pdf_data = urllib2.urlopen(pdf_url).read()
            filename = 'WEB_' + sponsor_ref + '_' + \
                child_code + '_' + str(time.time())[:10] + '.pdf'

            # Append a second (blank) page if necessary to the pdf
            pdf_letter = self.analyze_webletter(pdf_data)

            # here, "attachment" is the PDF
            # analyze "attachment" to check template and create image preview
            line_vals = func.analyze_attachment(
                self.env, pdf_letter, filename, template)[0]

            # Check UTM
            internet_id = self.env.ref('utm.utm_medium_website').id
            utms = self.env['utm.mixin'].get_utms(utm_source, utm_medium, utm_campaign)

            line_vals.update({
                'import_id': import_config.id,
                'partner_id': sponsor_id.id,
                'child_id': child_id.id,
                'letter_language_id': lang_id,
                'original_text': original_text,
                'source': 'website',
                'source_id': utms['source'],
                'medium_id': utms.get('medium', internet_id),
                'campaign_id': utms['campaign'],
                'email': email,
                'partner_name': name,
            })

            # Here, "attachment" is the image uploaded by the sponsor
            if attachment_url:
                attachment_data = urllib2.urlopen(attachment_url).read()
                filename_attachment = filename.replace(".pdf", ".%s" % ext)
                line_vals.update({
                    'original_attachment_ids': [(0, 0, {
                        'datas_fname': filename_attachment,
                        'datas': base64.b64encode(attachment_data),
                        'name': filename_attachment,
                        'res_model': 'import.letter.line',
                    })]
                })

            line_id = self.env['import.letter.line'].create(line_vals)

            import_config.import_completed = True
            logger.info("Try to copy file {} !".format(filename))
            # Copy file in attachment in the done letter folder
            share_nas = self.env.ref('sbc_switzerland.share_on_nas').value
            import_letter_path = self.env.ref(
                'sbc_switzerland.scan_letter_imported').value + filename

            file_pdf = BytesIO(pdf_letter)
            smb_conn = self._get_smb_connection()
            if smb_conn and smb_conn.connect(
                    SmbConfig.smb_ip, SmbConfig.smb_port):
                smb_conn.storeFile(share_nas, import_letter_path, file_pdf)

                # save eventual attachment
                if attachment_url:
                    logger.info("Try save attachment {} !"
                                .format(filename_attachment))

                    import_letter_path = self.env.ref(
                        'sbc_switzerland.scan_letter_imported').value + \
                        filename_attachment

                    file_attachment = BytesIO(attachment_data)
                    smb_conn.storeFile(
                        share_nas,
                        import_letter_path,
                        file_attachment)
                smb_conn.close()

            # Accept privacy statement
            sponsor_id.set_privacy_statement(origin='new_letter')

            return True
        except Exception as e:
            logger.error(str(e))
            logger.error("Failed to create webletter", exc_info=True)
            return False
