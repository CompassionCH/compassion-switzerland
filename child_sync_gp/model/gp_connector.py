# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from mysql_connector.model.mysql_connector import mysql_connector
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """

    # Mapping for child transfers to exit_reason_code in GP
    transfer_mapping = {
        'AU': '15',
        'CA': '16',
        'DE': '17',
        'ES': '38',
        'FR': '18',
        'GB': '20',
        'IT': '19',
        'KR': '37',
        'NL': '35',
        'NZ': '40',
        'US': '21',
        'NO': '42',
    }

    def upsert_child(self, uid, child):
        """Push or update child in GP after converting all relevant
        information in the destination structure."""
        name = child.name
        if child.firstname and name.endswith(child.firstname):
            name = name[:-len(child.firstname)]
        vals = {
            'CODE': child.code,
            'NOM': name,
            'PRENOM': child.firstname or '',
            'SEXE': child.gender,
            'DATENAISSANCE': child.birthdate,
            'SITUATION': child.state,
            'ID': self._get_gp_uid(uid),
            'COMPLETION_DATE': child.completion_date,
            'DATEDELEGUE': child.date_delegation,
            'CODEDELEGUE': child.delegated_to.ref,
            'REMARQUEDELEGUE': child.delegated_comment or '',
            'id_erp': child.id
        }
        if child.gp_exit_reason:
            vals['ID_MOTIF_FIN'] = int(child.gp_exit_reason)
        return self.upsert("Enfants", vals)

    def upsert_case_study(self, uid, case_study, create=False):
        """Push or update latest Case Study in GP."""
        id_fichier = False
        vals = {
            'COMMENTAIRE_FR': case_study.desc_fr or '',
            'COMMENTAIRE_DE': case_study.desc_de or '',
            'COMMENTAIRE_ITA': case_study.desc_it or '',
            'COMMENTAIRE_EN': case_study.desc_en or '',
            'IDUSER': self._get_gp_uid(uid),
            'CODE': case_study.code,
            'DATE_INFO': case_study.info_date,
        }
        if create:
            info_date_gp = self.selectOne(
                "SELECT MAX(DATE_INFO) AS date FROM Fichiersenfants "
                "WHERE CODE = %s", case_study.code).get('date', '1970-01-01')
            if info_date_gp == case_study.info_date:
                # Case study already exists on GP ->
                # Don't upsert it
                return False
            vals.update({
                'DATE_PHOTO': case_study.pictures_id.date,
                'DATE_IMPORTATION': datetime.today().strftime(DF)})
        if self.upsert("Fichiersenfants", vals):
            id_fichier = self.selectOne(
                "SELECT MAX(Id_Fichier_Enfant) AS id FROM Fichiersenfants "
                "WHERE Code = %s", case_study.code).get('id')
            if id_fichier:
                vals = {
                    'ID_DERNIER_FICHIER': id_fichier,
                    'CODE': case_study.child_id.code,
                    'id_erp': case_study.child_id.id}
                self.upsert("Enfants", vals)
        return id_fichier

    def upsert_project(self, uid, project):
        """Update a given Compassion project in GP."""
        closest_city = project.distance_from_closest_city_ids and \
            project.distance_from_closest_city_ids[0]

        location_en = closest_city and closest_city.value_en or ''
        location_fr = closest_city and closest_city.value_fr or location_en
        location_de = closest_city and closest_city.value_de or location_en
        location_it = closest_city and closest_city.value_it or location_en

        vals = {
            'CODE_PROJET': project.code,
            'DESCRIPTION_FR': project.description_fr or '',
            'DESCRIPTION_DE': project.description_de or '',
            'DESCRIPTION_EN': project.description_en or '',
            'DESCRIPTION_IT': project.description_it or '',
            'NOM': project.name,
            'IDUSER': self._get_gp_uid(uid),
            'DATE_MAJ': project.last_update_date,
            'SITUATION': self._get_project_state(project),
            'PAYS': project.code[:2],
            'LIEU_EN': location_en,
            'LIEU_FR': location_fr,
            'LIEU_DE': location_de,
            'LIEU_IT': location_it,
            'date_situation': project.status_date,
            'ProgramImplementorTypeCode': project.type,
            'StartDate': project.start_date,
            'LastReviewDate': project.last_update_date,
            'OrganizationName': project.local_church_name,
            'WesternDenomination': project.western_denomination,
            'CountryDenomination': project.country_denomination,
            'CommunityName': project.community_name,
            'disburse_gifts': project.disburse_gifts,
        }
        return self.upsert("Projet", vals)

    def _get_project_state(self, project):
        """ Returns the state of a project in GP format. """
        gp_state = 'Actif'
        if project.status == 'A':
            active_status_mapping = {
                'suspended': 'Suspension',
                'fund-suspended': 'Suspension avec retenue'}
            gp_state = active_status_mapping.get(project.suspension, 'Actif')
        elif project.status == 'P':
            gp_state = 'Phase out'
        elif project.status == 'T':
            gp_state = 'Terminé'
        return gp_state
