# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from __future__ import division
import base64
import StringIO
import contextlib
from collections import namedtuple
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from openerp import models, api, _
from openerp.tools.misc import mod10r

FontMeta = namedtuple('FontMeta', ('name', 'size'))


class PaymentSlip(models.Model):
    """"Add methods to print Christmas Payment Slip for partners"""

    _inherit = 'l10n_ch.payment_slip'

    @api.model
    def draw_christmas(self, partner, a4=False, out_format='PDF', scale=None,
                       b64=False, report_name=None):
        """Generate the payment slip image
        :param a4: If set to True will print on slip on a A4 paper format
        :type a4: bool

        :param out_format: output format at current time only PDF is supported
        :type out_format: str

        :param scale: scale quadratic ration
        :type scale: float

        :param b64: If set to True the output image string
                    will be encoded to base64

        :return: slip image string
        :rtype: str
        """
        if out_format != 'PDF':
            raise NotImplementedError(
                'Only PDF payment slip are supported'
            )
        partner.ensure_one()
        lang = partner.lang
        self = self.with_context(lang=lang)
        company = self.env.user.company_id
        print_settings = self._get_settings(report_name)
        self._register_fonts()
        default_font = self._get_text_font()
        small_font = self._get_samll_text_font()
        # amount_font = self._get_amount_font()
        scan_font = self._get_scan_line_text_font(company)
        bank_acc = self.env['res.partner.bank'].search([
            ('acc_number', '=', '01-44443-7')], limit=1)
        if a4:
            canvas_size = (595.27, 841.89)
        else:
            canvas_size = (595.27, 286.81)
        with contextlib.closing(StringIO.StringIO()) as buff:
            canvas = Canvas(buff,
                            pagesize=canvas_size,
                            pageCompression=None)
            self._draw_background(canvas, print_settings)
            canvas.setFillColorRGB(*self._fill_color)
            if a4:
                initial_position = (0.05 * inch,  4.50 * inch)
                self._draw_description_line(canvas,
                                            print_settings,
                                            initial_position,
                                            default_font)
            initial_position = (0.05 * inch, 1.4 * inch)
            self._draw_address(canvas, print_settings, initial_position,
                               default_font, partner)
            initial_position = (4.86 * inch, 2.2 * inch)
            self._draw_address(canvas, print_settings, initial_position,
                               default_font, partner)
            reference = self.compute_christmas_bvr_ref(partner)
            self._draw_ref(canvas,
                           print_settings,
                           (4.9 * inch, 2.70 * inch),
                           default_font,
                           reference)
            self._draw_recipe_ref(canvas,
                                  print_settings,
                                  (0.05 * inch, 1.6 * inch),
                                  small_font,
                                  reference)
            if bank_acc.print_bank:
                self._draw_bank(canvas,
                                print_settings,
                                (0.05 * inch, 3.7 * inch),
                                default_font,
                                bank_acc.bank)
                self._draw_bank(canvas,
                                print_settings,
                                (2.45 * inch, 3.7 * inch),
                                default_font,
                                bank_acc.bank)
            else:
                print_settings.bvr_add_vert += 0.15
                print_settings.bvr_message_vert += 0.1
            if bank_acc.print_partner:
                if (bank_acc.print_account or
                        bank_acc.bvr_adherent_num):
                    first_position = (0.05 * inch,  3.4 * inch)
                    second_position = (2.45 * inch, 3.4 * inch)
                else:
                    first_position = (0.05 * inch,  3.75 * inch)
                    second_position = (2.45 * inch, 3.75 * inch)
                self._draw_address(canvas, print_settings, first_position,
                                   default_font, bank_acc.partner_id,
                                   partner.lang)
                self._draw_address(canvas, print_settings, second_position,
                                   default_font, bank_acc.partner_id,
                                   partner.lang)
            num_car, frac_car = ("%.2f" % self.amount_total).split('.')
            # ################ Do not print any amount ##################
            # self._draw_amount(canvas, print_settings,
            #                   (1.48 * inch, 2.0 * inch),
            #                   amount_font, num_car)
            # self._draw_amount(canvas, print_settings,
            #                   (2.14 * inch, 2.0 * inch),
            #                   amount_font, frac_car)
            # self._draw_amount(canvas, print_settings,
            #                   (3.88 * inch, 2.0 * inch),
            #                   amount_font, num_car)
            # self._draw_amount(canvas, print_settings,
            #                   (4.50 * inch, 2.0 * inch),
            #                   amount_font, frac_car)
            if bank_acc.print_account:
                self._draw_bank_account(canvas,
                                        print_settings,
                                        (1 * inch, 2.35 * inch),
                                        default_font,
                                        bank_acc.get_account_number())
                self._draw_bank_account(canvas,
                                        print_settings,
                                        (3.4 * inch, 2.35 * inch),
                                        default_font,
                                        bank_acc.get_account_number())
            self._draw_message_christmas(canvas,
                                         print_settings,
                                         (0.05 * inch, 2.6 * inch),
                                         default_font,
                                         partner)
            self._draw_message_christmas(canvas,
                                         print_settings,
                                         (2.45 * inch, 2.6 * inch),
                                         default_font,
                                         partner)
            self._draw_scan_line_christmas(canvas,
                                           print_settings,
                                           (8.26 * inch - 4/10 * inch,
                                            4/6 * inch),
                                           scan_font, reference,
                                           bank_acc)
            self._draw_hook(canvas, print_settings)
            canvas.showPage()
            canvas.save()
            img_stream = buff.getvalue()
            if b64:
                img_stream = base64.encodestring(img_stream)
            return img_stream

    @api.model
    def _draw_message_christmas(self, canvas, print_settings,
                                initial_position, font, partner):
        x, y = initial_position
        x += print_settings.bvr_message_horz * inch
        y += print_settings.bvr_message_vert * inch
        canvas.setFont(font.name, font.size)
        canvas.drawString(x, y,
                          self._compute_message_christmas(partner.lang))

    @api.model
    def _compute_message_christmas(self, language):
        # Should be maximal 25 characters long!
        return {
            'fr_CH': 'Fonds Cadeaux Noël',
            'de_DE': 'Fonds Weihnachtsgeschenke',
            'it_IT': 'Fondo Regali di Natale',
            'en_US': 'Christmas Gift Fund'
        }.get(language, 'Christmas Gift Fund')[:25]

    @api.model
    def _draw_address(self, canvas, print_settings, initial_position, font,
                      com_partner, lang=None):
        x, y = initial_position
        x += print_settings.bvr_add_horz * inch
        y += print_settings.bvr_add_vert * inch
        text = canvas.beginText()
        text.setTextOrigin(x, y)
        text.setFont(font.name, font.size)
        text.textOut(com_partner.name)
        text.moveCursor(0.0, font.size)
        for line in com_partner.contact_address.split("\n"):
            if not line.strip():
                continue
            if len(line) >= 4 and line[-4].isdigit():
                state = line[0:-4].strip()
                postal_code = line[-4:].strip()
                line = postal_code + ' ' + state
            if line == 'Switzerland' or line == 'Svizzera' or line == \
                    'Suisse' or line == 'Schweiz':
                line = self._compute_country(lang or com_partner.lang)
            text.textLine(line)
        canvas.drawText(text)

    @api.model
    def _compute_country(self, language):
        return {
            'fr_CH': 'Suisse',
            'de_DE': 'Schweiz',
            'it_IT': 'Svizzera',
            'en_US': 'Switzerland'
        }.get(language, 'Switzerland')[:25]

    @api.model
    def _compute_scan_line_christmas(self, reference, bank):
        """Generate a list containing all element of scan line

        the element are grouped by char or symbol

        This will allows the free placment of each element
        and enable a fine tuning of spacing

        :return: a list of sting representing the scan bar

        :rtype: list
        """
        line = []
        line += "042"
        line.append('>')
        line += [char for char in reference.replace(" ", "")]
        line.append('+')
        line.append(' ')
        bank = bank.get_account_number()
        account_components = bank.split('-')
        if len(account_components) != 3:
            raise Warning(_('Please enter a correct postal number like: '
                            '01-23456-1'))
        bank_identifier = "%s%s%s" % (
            account_components[0],
            account_components[1].rjust(6, '0'),
            account_components[2]
        )
        line += [car for car in bank_identifier]
        line.append('>')
        return line

    @api.model
    def _draw_scan_line_christmas(self, canvas, print_settings,
                                  initial_position, font, reference, bank):
        """Draw reference on canvas

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        """
        x, y = initial_position
        x += print_settings.bvr_scan_line_horz * inch
        y += print_settings.bvr_scan_line_vert * inch
        canvas.setFont(font.name, font.size)
        for car in self._compute_scan_line_christmas(reference, bank)[::-1]:
            canvas.drawString(x, y, car)
            # some font type return non numerical
            x -= 0.1 * inch

    @api.model
    def compute_christmas_bvr_ref(self, partner):
        """ Generates a Christmas BVR Reference.
        See file \\nas\it\devel\Code_ref_BVR.xls for more information."""
        result = '0' * (9 + (7 - len(partner.ref))) + partner.ref
        result += '0' * 5
        # Type '7' = Campaign
        result += '7'
        # 0023 is Fund ID for Christmas Fund
        result += '0023'
        if len(result) == 26:
            return self._space(mod10r(result))
