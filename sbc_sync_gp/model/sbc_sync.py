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


class sbcSync(orm.Model):
    _inherit = 'res.config.installer'
    _name = 'sbc.sync'

    test = fields.Char('Hello world')
    sss