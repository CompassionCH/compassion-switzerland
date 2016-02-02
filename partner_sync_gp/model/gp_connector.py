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

from openerp import fields
from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields.
    """

    # Used to map Postgres columns to MySQL columns. The update method will
    # automatically translate fields that are listed in this dictionary.
    # The commented mappings are treated specifically by a method that needs
    # to read several fields value in order to perform a correct mapping.
    colMapping = {
        'ref': 'codega',
        'lang': 'langue_parrain',
        'street': 'rue',
        'street2': 'rue2',
        'street3': 'rue3',
        'city': 'commune',
        'zip': 'codepostal',
        'country_id': 'codepays',
        'title': 'titre',
        'function': 'metier',
        'email': 'e_mail',
        'website': 'web',
        'fax': 'numfax',
        'phone': 'teldom',
        'create_date': 'datecreation',
        'write_date': 'datemodif',
        'mobile': 'telmobile',
        'lastname': 'nom',
        'firstname': 'prenom',
        'church_id': 'eglise',
        'church_unlinked': 'eglise',
        'deathdate': 'datedeces',
        'nbmag': 'nbsel',
        'birthdate': 'anneenaissance',
        'tax_certificate': 'recu_annuel',
        'thankyou_letter': 'recu_immediat',
        'calendar': 'calendrier',
        'christmas_card': 'carte_noel',
        'birthday_reminder': 'rappel_anniversaire',
        'id': 'id_erp',
    }

    # This gives the MySQL Sponsor Category ids corresponding to the Category
    # Names defined in OpenERP.
    # Please ensure that the mapping is up to date and correct (this saves a
    # lot of useless queries).
    catMapping = {
        'Donor': '1',
        'Sponsor': '2',
        'Ambassador': '3',
        'Church': '4',
        'Translator': '5',
        'Complete Mailing': '6',
        'Abroad': '7',
        'Correspondance Program': '8',
        'Correspondance by Compassion': '9',
        'Old Sponsor': '10'
    }

    # Gives the language in the format stored in the MySQL database.
    langMapping = {
        'fr_CH': 'fra',
        'fr_FR': 'fra',
        'de_DE': 'deu',
        'en_US': 'eng',
        'en_UK': 'eng',
        'it_IT': 'ita',
        'es_ES': 'esp'
    }

    # Gives the corresponding title ID in the MySQL database.
    titleMapping = {
        'Mister': '1',
        'Madam': '2',
        'Misters': '4',
        'Ladies': '5',
        'Mister and Madam': '7',
        'Family': '8',
        'Doctor': '9',
        'Pastor': '10',
        'Friends of Compassion': '11'
    }

    def upsert_partner(self, partner, categories, uid):
        """ Update fields in GP given the partner.

            :param: categories (list): full names of the partner's
                                       categories.
        """
        gp_vals = {'IDUSER': self._get_gp_uid(uid)}
        mapping = self.colMapping.copy()
        parent = False
        if partner.is_company:
            if partner.child_ids:
                parent = True
                # Only update the Company name, all other info are in the
                # contact partner
                mapping = {
                    'ref': 'codega',
                    'lastname': 'raissociale'}
            else:
                del mapping['firstname']
                mapping['lastname'] = 'raissociale'

        for field_name in mapping.iterkeys():
            value = getattr(partner, field_name)
            # Convert the language
            if field_name == 'lang':
                value = self.langMapping[value]
            # Convert the country code (use the code instead of the id)
            elif field_name == 'country_id':
                value = partner.country_id.code or 'CH'
            # Convert the title (use the correct ids found in the MySQL
            # database)
            elif field_name == 'title':
                value = self.titleMapping.get(partner.title.name, '11')
            # Convert the church (use the reference number instead of the id)
            elif field_name == 'church_id':
                value = partner.church_id.ref
            # Sometimes create_date is missing
            elif field_name == 'create_date':
                if not value:
                    value = partner.date or fields.Date.context_today()
            # Convert the receipts
            elif field_name in ('tax_certificate', 'thankyou_letter'):
                if value == 'no':
                    value = '0'
                elif value == 'paper':
                    value = '1'
                elif value == 'email':
                    value = '2'
                else:
                    value = '3'

            if value or isinstance(partner._fields[field_name],
                                   fields.Boolean):
                gp_vals[mapping[field_name]] = value
            else:
                gp_vals[mapping[field_name]] = '' if isinstance(
                    partner._fields[field_name], fields.Char) else None

        self.upsert("Adresses", gp_vals)

        # Update the categories in GP
        if not parent:
            self._updateCategories(partner.ref, categories)
            self._updateBooleanCategory(partner.ref, 'Abroad', partner.abroad)
            self._updateBooleanCategory(
                partner.ref, 'Complete Mailing', not partner.opt_out)
            self._update_spoken_langs(partner)

        return True

    def _updateCategories(self, ref, categories, deleteAbsent=True):
        """ Given a partner reference and his category names, update the
        MySQL Categories_adresses Table. """
        oldCategoryIds = []
        # Convert the list of category names into a list of category ids used
        # in the MySQL table (-1 if not found).
        currentCatIds = map(lambda catName: int(self.catMapping[catName])
                            if catName in self.catMapping.keys()
                            else -1, categories)

        for row in self.selectAll("SELECT ID_CAT FROM Categories_adresses "
                                  "WHERE CODEGA = %s AND DATE_FIN IS NULL",
                                  ref):
            catId = row["ID_CAT"]
            oldCategoryIds.append(catId)
            # If the category is no more present, remove it (by setting an end
            # date), except for "Mailing Complet" and "Abroad" which are
            # treated separately (boolean categories).
            if deleteAbsent and catId not in currentCatIds and catId not in (
               int(self.catMapping["Complete Mailing"]),
               int(self.catMapping["Abroad"])):
                self.query(
                    "UPDATE Categories_adresses SET DATE_FIN = NOW() "
                    "WHERE CODEGA = %s AND ID_CAT = %s", (ref, catId))

        # Add current categories that are not already present in the MySQL
        # table.
        sqlInsert = "INSERT INTO Categories_adresses(CODEGA,ID_CAT," \
                    "Date_Ajout) VALUES (%s,{0},now())"
        sqlUpdate = "UPDATE Categories_adresses SET DATE_AJOUT = NOW(), " \
                    "DATE_FIN = NULL WHERE CODEGA = %s AND ID_CAT = {0}"
        for category in currentCatIds:
            if category > 0 and category not in oldCategoryIds:
                if self.selectOne("SELECT ID_CAT FROM Categories_adresses "
                                  "WHERE CODEGA = %s AND ID_CAT = %s",
                                  (ref, category)):
                    self.query(sqlUpdate.format(category), ref)
                else:
                    self.query(sqlInsert.format(category), ref)

    def _updateBooleanCategory(self, ref, categoryName, activeStatus):
        """ Given a partner reference and his boolean category status,
        update the MySQL Categories_adresses Table.
        Currently, this method is used for the 'Mailing Complet' (=opt_out)
        and 'A l'étranger/e-mail' (=abroad) Categories.
        """
        catId = self.catMapping[categoryName]
        if activeStatus:
            if self.selectOne("SELECT ID_CAT FROM Categories_adresses "
                              "WHERE CODEGA = %s AND ID_CAT = %s",
                              (ref, catId)):
                sql = "UPDATE Categories_adresses SET Date_Ajout = NOW(), " \
                      "DATE_FIN = NULL WHERE CODEGA = %s AND ID_CAT = %s"
            else:
                sql = "INSERT INTO Categories_adresses(CODEGA,ID_CAT," \
                      "Date_Ajout) VALUES (%s,%s,now())"
        else:
            sql = "UPDATE Categories_adresses SET DATE_FIN = NOW() " \
                  "WHERE CODEGA = %s AND ID_CAT = %s"
        return self.query(sql, (ref, catId))

    def _update_spoken_langs(self, partner):
        """ Update the langs of a partner in GP. """
        self.query("Delete from langueparlee where codega = %s",
                   [partner.ref])
        for lang in partner.spoken_lang_ids:
            self.query(
                "insert into langueparlee(codega, idlangues) values(%s, %s)",
                [partner.ref, lang.code_iso])

    def nextRef(self):
        """ Gives the next valid value for the CODEGA sequence field """
        result = self.selectOne(
            "SELECT currval FROM sequences WHERE nom = 'CODEGA'")
        if result:
            self.query(
                "UPDATE sequences SET currval = currval+1 "
                "WHERE nom = 'CODEGA'")
            return result['currval'] + 1

    def linkContact(self, uid, company_ref, contact_id):
        """ Link a contact to a company and use one single line address for
        both in the MySQL Table.
        Args:
            company_ref (string) : the reference of the company partner
                                   in MySQL
            contact_id (long) : the id of the contact in OpenERP
        """
        return self.query("UPDATE Adresses SET id_erp = %s, IDUSER = %s "
                          "WHERE CODEGA = %s",
                          (contact_id, self._get_gp_uid(uid), company_ref))

    def unlinkContact(self, uid, company, company_categories):
        """ Unlink a contact from a company and use two different addresses
        in the MySQL Table.
        Args:
            company (res.partner) : the company partner
            company_categories (list) : the category names of the company,
                                        in order to restore them and remove
                                        the categories of the contact.
        """
        sql = "UPDATE Adresses SET id_erp = {0}, PRENOM='', NOM='', " \
              "TITRE=NULL, TELMOBILE='', LANGUE_PARRAIN='{2}', "\
              "IDUSER = '{3}' " \
              "WHERE CODEGA = '{1}'".format(company.id, company.ref,
                                            self.langMapping[company.lang],
                                            self._get_gp_uid(uid))
        self.query(sql)
        self._updateCategories(company.ref, company_categories)
        self._updateBooleanCategory(
            company.ref, 'Complete Mailing', not company.opt_out)
        self._updateBooleanCategory(company.ref, 'Abroad', company.abroad)

    def unlink(self, uid, id):
        """ Unlink a partner in MySQL. """
        return self.query("UPDATE Adresses SET id_erp=NULL, IDUSER = '{0}' "
                          "WHERE id_erp={1}".format(self._get_gp_uid(uid),
                                                    id))

    def changeToCompany(self, uid, partner_id, name):
        """ Changes the selected partner in MySQL so that it becomes a
        company.
        Args:
            ref (string) : the reference of the partner in MySQL
        """
        return self.query("UPDATE Adresses SET PRENOM='', NOM='', TITRE=NULL,"
                          "RAISSOCIALE = '{2}', IDUSER = '{0}' "
                          "WHERE ID_ERP={1}".format(self._get_gp_uid(uid),
                                                    partner_id, name))

    def changeToPrivate(self, uid, partner_id):
        """ Changes the selected partner in MySQL so that it is no
        more a company.
        Args:
            ref (string) : the reference of the partner in MySQL
        """
        return self.query("UPDATE Adresses SET RAISSOCIALE='', IDUSER = '{0}'"
                          " WHERE ID_ERP={1}".format(self._get_gp_uid(uid),
                                                     partner_id))

    def getRefContact(self, id):
        """ Returns the reference of the partner in MySQL that has"
        id_erp pointing to the id given (returns -1 if not found). """
        res = self.selectOne(
            "SELECT CODEGA FROM Adresses WHERE id_erp = {0}".format(id))
        return res['CODEGA'] if res else -1
