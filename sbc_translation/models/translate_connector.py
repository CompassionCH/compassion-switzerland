# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import datetime

from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector


class TranslateConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields.
    """

    def __init__(self):
        super(TranslateConnect, self).__init__('mysql_translate_host',
                                               'mysql_translate_user',
                                               'mysql_translate_pw',
                                               'mysql_translate_db')
        self.current_time =datetime.datetime.now()

    def upsert_text(self, sponsorship, letter):
        """Push or update text (db table) on local translate plateforme
        """

        child = sponsorship.child_id
        sponsor = sponsorship.partner_id

        self.letter_name = "_".join((child.code, sponsor.ref, str(letter.id)))
        child_age = datetime.date.today().year - int(child.birthdate[:4])

        src_lang_id = self.getLanguageId(letter.original_language_id.code_iso)
        aim_lang_id = self.getLanguageId(sponsorship.reading_language.code_iso)

        vals = {
            'src_lang_id': src_lang_id,
            'aim_lang_id': aim_lang_id,
            'title': self.letter_name,
            'file': self.letter_name + '.pdf',
            'codega': sponsor.ref,
            'gender': sponsor.title.name,
            'name': sponsor.name,
            'firstname': sponsor.firstname,
            'code': child.code,
            'kid_name': child.name,
            'kid_firstname': child.firstname,
            'age': child_age,
            'kid_gender': child.gender,
            'createdat': self.current_time,
            'updatedat': self.current_time,
        }
        return self.upsert("text", vals)

    def upsert_translation(self, text_id):
        """Push or update translation (db table) on local translate plateforme
        """

        vals = {
            'file': self.letter_name + '.tif',
            'text_id': text_id,
            'createdat': self.current_time,
            'updatedat': self.current_time,
            'toDo_id': 0,
        }
        return self.upsert("translation", vals)

    def upsert_translation_status(self, translation_id, status):
        """Push or update translation_status (db table) on local translate
        plateforme
        """

        vals = {
            'translation_id': translation_id,
            'status_id': status,
            'createdat': self.current_time,
            'updatedat': self.current_time,
        }
        return self.upsert("translation_status", vals)

    def getLanguageId(self, language_iso_code):
        """ Returns the reference of the partner in MySQL that has"
        id_erp pointing to the id given (returns -1 if not found). """
        res = self.selectOne(
            "SELECT id FROM language WHERE GP_Libel LIKE '{}'"
            .format(language_iso_code))
        return res['id'] if res else -1
