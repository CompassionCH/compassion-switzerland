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
from openerp.tools.config import config
from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector
from datetime import datetime
from smb.SMBConnection import SMBConnection
import logging
import sys

logger = logging.getLogger(__name__)


class GPConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by GP, as well as all mappings
        from OpenERP fields to corresponding MySQL fields. """

    def upsert_child(self, uid, child):
        """Push or update child in GP after converting all relevant
        information in the destination structure."""
        name = ''
        if child.name:
            name = child.name.replace(child.firstname, '', 1).strip()
        vals = {
            'CODE': child.local_id,
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

    def upsert_case_study(self, uid, child, create=False):
        """Push or update latest Case Study in GP."""
        id_fichier = False
        info_date = child.pictures_ids[0].date
        vals = {
            'COMMENTAIRE_FR': child.desc_fr or '',
            'COMMENTAIRE_DE': child.desc_de or '',
            'COMMENTAIRE_ITA': child.desc_it or '',
            'COMMENTAIRE_EN': child.desc_en or '',
            'IDUSER': self._get_gp_uid(uid),
            'CODE': child.local_id,
            'DATE_INFO': info_date,
        }
        if create:
            info_date_gp = self.selectOne(
                "SELECT MAX(DATE_INFO) AS date FROM Fichiersenfants "
                "WHERE CODE = %s",
                child.local_id).get('date', '1970-01-01')
            if info_date_gp == info_date:
                # Case study already exists on GP ->
                # Don't upsert it
                return False
            vals.update({
                'DATE_PHOTO': info_date,
                'DATE_IMPORTATION': datetime.today().strftime(DF)})
        if self.upsert("Fichiersenfants", vals):
            id_fichier = self.selectOne(
                "SELECT MAX(Id_Fichier_Enfant) AS id FROM Fichiersenfants "
                "WHERE Code = %s", child.local_id).get('id')
            if id_fichier:
                vals = {
                    'ID_DERNIER_FICHIER': id_fichier,
                    'CODE': child.local_id,
                    'id_erp': child.id}
                self.upsert("Enfants", vals)
        return id_fichier

    def upsert_project(self, uid, project):
        """Update a given Compassion project in GP."""
        # Solve the encoding problems on child's descriptions
        reload(sys)
        sys.setdefaultencoding('UTF8')

        vals = {
            'CODE_PROJET': project.icp_id,
            'DESCRIPTION_FR': project.description_fr or '',
            'DESCRIPTION_DE': project.description_de or '',
            'DESCRIPTION_EN': project.description_en or '',
            'DESCRIPTION_IT': project.description_it or '',
            'NOM': project.name,
            'IDUSER': self._get_gp_uid(uid),
            'DATE_MAJ': project.last_update_date,
            'SITUATION': self._get_project_state(project),
            'PAYS': project.icp_id[:2],
            'LIEU_EN': project.community_name or '',
            'LIEU_FR': project.community_name or '',
            'LIEU_DE': project.community_name or '',
            'LIEU_IT': project.community_name or '',
            'date_situation': project.status_date,
            'ProgramImplementorTypeCode': project.type,
            'StartDate': project.partnership_start_date,
            'LastReviewDate': project.last_update_date,
            'OrganizationName': project.local_church_name or '',
            'CountryDenomination': project.country or '',
            'CommunityName': project.community_name or '',
            'disburse_gifts': not project.hold_gifts,
        }
        return self.upsert("Projet", vals)

    def transfer(self, uid, old_code, new_code):
        """ Sync a child transfer with GP: rename pictures and log a note. """
        # Retrieve configuration
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            return False

        # Rename files in shared folder
        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            gp_old_pic_path = "{0}{1}/".format(config.get('gp_pictures'),
                                               old_code[:2])
            gp_new_pic_path = "{0}{1}/".format(config.get('gp_pictures'),
                                               new_code[:2])
            pic_files = smb_conn.listPath('GP', gp_old_pic_path)
            for file in pic_files:
                filename = file.filename
                if filename.startswith(old_code):
                    new_name = filename.replace(old_code, new_code)
                    smb_conn.rename('GP', gp_old_pic_path + filename,
                                    gp_new_pic_path + new_name)

        # Rename child code in Poles table
        self.query("UPDATE Poles SET CODESPE = %s WHERE CODESPE = %s",
                   [old_code, new_code])
        return True

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
