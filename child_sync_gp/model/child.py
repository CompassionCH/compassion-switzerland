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

from openerp.osv import orm
from openerp.tools.config import config

from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure
from tempfile import TemporaryFile

from . import gp_connector
import base64


class child_compassion(orm.Model):
    _inherit = 'compassion.child'

    def create(self, cr, uid, vals, context=None):
        new_id = super(child_compassion, self).create(cr, uid, vals, context)
        child = self.browse(cr, uid, new_id, context)
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_child(uid, child)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        """Update GP with the last information of the child."""
        res = super(child_compassion, self).write(cr, uid, ids, vals, context)
        if not isinstance(ids, list):
            ids = [ids]
        gp_connect = gp_connector.GPConnect()

        for child in self.browse(cr, uid, ids, context):
            gp_connect.upsert_child(uid, child)

        return res


class child_property(orm.Model):
    """ Upsert Case Studies """
    _inherit = 'compassion.child.property'

    def write(self, cr, uid, ids, vals, context=None):
        super(child_property, self).write(cr, uid, ids, vals, context)
        for case_study in self.browse(cr, uid, ids, context):
            create_mode = 'pictures_id' in vals
            self._upsert_gp(uid, case_study, create_mode)
        return True

    def _upsert_gp(self, uid, case_study, create_mode):
        # We only push case studies with a picture attached to it
        gp_connect = gp_connector.GPConnect()
        if case_study.pictures_id:
            return gp_connect.upsert_case_study(uid, case_study, create_mode)
        return False

    def attach_pictures(self, cr, uid, ids, pictures_id, context=None):
        """ Push the new picture. """
        res = super(child_property, self).attach_pictures(
            cr, uid, ids, pictures_id, context)

        pictures = self.pool.get('compassion.child.pictures').browse(
            cr, uid, pictures_id, context)

        # Retrieve configuration
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            raise orm.except_orm(
                'Config Error',
                'Missing Samba configuration in conf file.')
        child = pictures.child_id

        date_pic = pictures.date.replace('-', '')
        gp_pic_path = "{0}{1}/".format(config.get('gp_pictures'),
                                       child.code[:2])
        file_name = "{0}_{1}.jpg".format(child.code, date_pic)
        picture_file = TemporaryFile()
        picture_file.write(base64.b64decode(pictures.fullshot))
        picture_file.flush()
        picture_file.seek(0)

        # Upload file to shared folder
        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            try:
                smb_conn.storeFile(
                    'GP', gp_pic_path + file_name, picture_file)
            except OperationFailure:
                # Directory may not exist
                smb_conn.createDirectory('GP', gp_pic_path)
                smb_conn.storeFile(
                    'GP', gp_pic_path + file_name, picture_file)
        return res
