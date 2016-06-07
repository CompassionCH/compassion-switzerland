# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields
from openerp.exceptions import Warning
from openerp.tools.config import config

from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure
from tempfile import TemporaryFile

from . import gp_connector
import base64


class ChildCompassion(models.Model):
    _inherit = 'compassion.child'

    GP_EXIT_MAPPING = {
        'Reached Maximum Age': '41',
        'Reached the end of the relevant programs available at the church '
        'partner': '39',
        'Child / Caregiver does not comply with policies': '36',
        'Child in system under two numbers (enter other number in the '
        'Comments box below)': '1',
        'Child places others at risk': '36',
        'Child sponsored by another organization': '31',
        'Death of caregiver creates situation where child cannot continue':
            '1',
        'Death of child': '13',
        'Family Circumstances Have Changed Positively So That Child No '
            'Longer Needs Compassion\'s Assistance': '29',
        'Family moved where a Compassion project with relevant programs is '
            'not available': '14',
        'Project or program closure': '26',
        'Taken out of project by parents, or family no longer interested '
            'in program': '30',
        'Unjustified absence from program activities for Greater Than 2 '
            'months': '22',
    }

    gp_exit_reason = fields.Char(compute='_get_gp_exit_reasons')

    def _get_gp_exit_reasons(self):
        # Maps exit reason for GP.
        for child in self:
            if child.exit_reason:
                child.gp_exit_reason = self.GP_EXIT_MAPPING[
                    child.gp_exit_reason]

    @api.model
    def create(self, vals):
        child = super(ChildCompassion, self).create(vals)
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_child(self.env.uid, child)
        return child

    @api.multi
    def write(self, vals):
        """Update GP with the last information of the child."""
        gp_connect = gp_connector.GPConnect()
        if 'local_id' in vals:
            for child in self:
                gp_connect.transfer(self.env.uid, child.local_id,
                                    vals['local_id'])

        res = super(ChildCompassion, self).write(vals)

        for child in self:
            gp_connect.upsert_child(self.env.uid, child)

        if 'desc_en' in vals or 'desc_fr' in vals or 'desc_de' in vals or \
                'desc_it' in vals:
            for child in self:
                gp_connect.upsert_case_study(self.env.uid, child)

        return res


class ChildPictures(models.Model):
    """ Create new Case Study when new pictures are downloaded. """
    _inherit = 'compassion.child.pictures'

    @api.model
    def create(self, vals):
        pictures = super(ChildPictures, self).create(vals)
        pictures._push_pictures()
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_case_study(self.env.uid, pictures.child_id,
                                     create=True)
        return pictures

    def _push_pictures(self):
        """ Push the new picture into the NAS for GP. """

        # Retrieve configuration
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            raise Warning(
                'Config Error',
                'Missing Samba configuration in conf file.')
        child = self.child_id

        date_pic = self.date.replace('-', '')
        gp_pic_path = "{0}{1}/".format(config.get('gp_pictures'),
                                       child.unique_id[:2])
        file_name = "{0}_{1}.jpg".format(child.unique_id, date_pic)
        picture_file = TemporaryFile()
        picture_file.write(base64.b64decode(self.fullshot))
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
