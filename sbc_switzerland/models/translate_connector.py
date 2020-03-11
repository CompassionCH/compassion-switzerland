##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime
from odoo.addons.mysql_connector.models.mysql_connector \
    import MysqlConnector
from odoo import fields


class TranslateConnect(MysqlConnector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by translate platform, as well as all mappings
        from OpenERP fields to corresponding MySQL fields.
    """

    def __init__(self):
        super().__init__(
            'mysql_translate_host',
            'mysql_translate_user',
            'mysql_translate_pw',
            'mysql_translate_db')

        self.current_time = datetime.datetime.now()

    def upsert_text(self, correspondence, file_name,
                    src_lang_id, dst_lang_iso):
        """Push or update text (db table) on local translate platform
        """
        child = correspondence.child_id
        sponsor = correspondence.partner_id

        self.letter_name = file_name
        child_age = datetime.date.today().year - int(child.birthdate[:4])

        text_type_id = 2 if correspondence.direction ==\
            'Supporter To Beneficiary' else 1

        first_letter_id = correspondence.env.ref(
            'sbc_compassion.correspondence_type_new_sponsor').id
        final_letter_id = correspondence.env.ref(
            'sbc_compassion.correspondence_type_final').id
        today = datetime.date.today()
        letter_age = (today - fields.Date.from_string(
            correspondence.scanned_date)).days
        # Each 15 days aging -> augment priority by 1
        priority = min((letter_age // 15) + 1, 4)
        type_ids = correspondence.communication_type_ids.ids
        if first_letter_id in type_ids or final_letter_id in type_ids:
            priority = 4

        vals = {
            'src_lang_id': src_lang_id,
            'aim_lang_id': dst_lang_iso,
            'title': self.letter_name,
            'file': self.letter_name,
            'codega': sponsor.ref,
            'gender': sponsor.title.name,
            'name': sponsor.name,
            'firstname': sponsor.firstname,
            'code': child.local_id,
            'kid_name': child.name,
            'kid_firstname': child.preferred_name,
            'age': child_age,
            'kid_gender': child.gender,
            'createdat': fields.Datetime.to_string(self.current_time),
            'updatedat': fields.Datetime.to_string(self.current_time),
            'priority_id': priority,
            'text_type_id': text_type_id,
        }
        return self.upsert("text", vals)

    def upsert_translation(self, text_id, letter):
        """Push or update translation (db table) on local translate platform
        """
        vals = {
            'file': self.letter_name[0:-4] + '.rtf',
            'text_id': text_id,
            'createdat': fields.Datetime.to_string(self.current_time),
            'updatedat': fields.Datetime.to_string(self.current_time),
            'toDo_id': 0,
            'letter_odoo_id': letter.id,
        }
        return self.upsert("translation", vals)

    def upsert_translation_status(self, translation_id):
        """Push or update translation_status (db table) on local translate
        platform
        """
        to_translate = 1
        vals = {
            'translation_id': translation_id,
            'status_id': to_translate,
            'createdat': fields.Datetime.to_string(self.current_time),
            'updatedat': fields.Datetime.to_string(self.current_time),
        }
        return self.upsert("translation_status", vals)

    def get_lang_id(self, lang_compassion_id):
        """ Returns the language's id in MySQL that has  GP_Libel pointing
         to the iso_code given (returns -1 if not found). """
        res = self.select_one(
            "SELECT id FROM language WHERE GP_Libel LIKE "
            "%s", lang_compassion_id.code_iso)
        return res['id'] if res else -1

    def get_translated_letters(self):
        """ Returns a list for dictionaries with translation and filename
        (sponsorship_id is in the file name...) in MySQL translation_test
        database that has translation_status to 'Traduit" (id = 3) and
        toDo_id to 'Pret' (id = 3)
        (returns -1 if not found). """
        res = self.select_all("""
            SELECT tr.id, tr.letter_odoo_id, tr.text, txt.id AS text_id,
            ld.GP_libel AS target_lang, usr.number AS translator,
            ls.GP_libel AS src_lang

            FROM translation_status trs
            INNER JOIN translation tr ON trs.translation_id = tr.id
            INNER JOIN user usr ON tr.user_id = usr.id
            INNER JOIN text txt ON tr.text_id = txt.id
            INNER JOIN language ld ON txt.aim_lang_id = ld.id
            INNER JOIN language ls ON txt.src_lang_id = ls.id
            WHERE tr.letter_odoo_id IS NOT NULL
            AND trs.status_id = 3
            AND tr.toDo_id = 3
        """)
        return res

    def update_translation_to_not_in_odoo(self, translation_id):
        """update translation to set toDo_id in state "Pas sur Odoo"
        """

        vals = {
            'id': translation_id,
            'toDo_id': 5,
            'updatedat': fields.Datetime.to_string(self.current_time),
        }
        return self.upsert("translation", vals)

    def update_translation_to_treated(self, translation_id):
        """update translation to set toDo_id in state "Traité"
        """

        vals = {
            'id': translation_id,
            'toDo_id': 4,
            'updatedat': fields.Datetime.to_string(self.current_time),
        }
        return self.upsert("translation", vals)

    def remove_letter(self, text_id):
        """ Delete a letter record with the text_id given """
        self.remove_from_text(text_id)

    def remove_from_text(self, text_id):
        """ Delete a text record for the text_id given """
        self.query("DELETE FROM text WHERE id=%s", text_id)

    def remove_translation_with_odoo_id(self, text_id):
        self.query("DELETE text FROM text INNER JOIN translation ON text.id\
             = translation.text_id WHERE translation.letter_odoo_id = %s", text_id)

    def get_server_uptime(self):
        return self.select_one("SHOW GLOBAL STATUS LIKE 'Uptime' ")

    def upsert_user(self, partner, create):
        """ Push or update an user (db table) on local translate platform """
        language_match = {
            'fr_CH': '1',
            'de_DE': '2',
            'it_IT': '3',
            'en_US': '1'
        }
        vals = {
            'number': partner.ref,
            'username': partner.ref,
            'email': partner.email,
            'alertTranslator': 1,
            'firstname': partner.firstname,
            'lastname': partner.lastname,
            'gender': partner.title.display_name,
            'language_id': language_match[partner.lang],
            'updatedat': fields.Datetime.context_timestamp(
                partner, self.current_time).replace(tzinfo=None),
        }
        if create:
            vals['code'] = None
            vals['createdat'] = fields.Datetime.context_timestamp(
                partner, self.current_time).replace(tzinfo=None)
            vals['isadmin'] = '0'
        return self.upsert("user", vals)

    def remove_user(self, partner):
        """ Delete a user """
        return self.query("DELETE FROM user WHERE number= %s", partner.ref)

    def disable_user(self, partner):
        vals = {
            'number': partner.ref,
            'username': None,
            'email': None,
            'password': None,
            'code': None,
            'alertTranslator': 0,
            'last_login': None,
            'updatedat': fields.Datetime.context_timestamp(
                partner, self.current_time).replace(tzinfo=None),
        }
        return self.upsert("user", vals)
