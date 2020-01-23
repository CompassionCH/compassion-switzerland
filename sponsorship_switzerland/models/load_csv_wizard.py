##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samy Bucher <samy.bucher@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import csv

from odoo import api, models, fields
import io


class LoadCsvWizard(models.TransientModel):
    _name = 'load.csv.wizard'
    _description = "Link gifts with letters"

    data_csv = fields.Binary('csv file')
    name_data_csv = fields.Char('File Name')

    @api.multi
    def link_gift2letters(self):
        for wizard in self:
            f = io.StringIO(wizard.data_csv.decode('base64')
                            .decode('utf-8-sig').encode('utf-8'))
            reader = csv.reader(f, delimiter=';')
            reader.next()
            for row in reader:
                letter = self.env['correspondence'].search([
                    ('kit_identifier', '=', row[0])
                ])
                gift = self.env['sponsorship.gift'].search([
                    # Dropping the 3 first characters to get the ID
                    # ex. CH-12345 -> 12345
                    ('id', '=', row[2][3:])
                ])
                if letter.gift_id and gift.letter_id:
                    continue
                if gift and letter:
                    gift.letter_id = letter
                    letter.gift_id = gift
        return True
