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

logger = logging.getLogger(__name__)


class GPConnect(mysql_connector):
   