# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import json
import sys
import calendar

from openerp.osv import orm

from sync_typo3 import Sync_typo3
from datetime import datetime


class compassion_project(orm.Model):
    _inherit = 'compassion.project'

    def _set_suspension_state(self, cr, uid, ids, context=None):
        for project in self.read(cr, uid, ids, ['code', 'suspension'],
                                 context):
            if project['suspension'] in ['suspended', 'fund-suspended']:
                # Remove children from internet
                child_obj = self.pool.get('compassion.child')
                child_ids = child_obj.search(cr, uid, [
                    ('code', 'like', project['code']),
                    ('state', '=', 'I')], context=context)
                if child_ids:
                    child_obj.child_remove_from_wordpress(cr, uid, child_ids,
                                                          context)
        super(compassion_project, self)._set_suspension_state(
            cr, uid, ids, context)

    def get_project_from_typo3(self, cr, uid, project_code):
        res = json.loads(Sync_typo3.request_to_typo3(
            "select * "
            "from tx_drechildpoolmanagement_domain_model_projects "
            "where project_key='%s'" % project_code, 'sel'))
        if res:
            return res[0]['uid']

        return False

    def project_add_to_typo3(self, cr, uid, ids, context=None):
        # Solve the encoding problems on child's descriptions
        reload(sys)
        sys.setdefaultencoding('UTF8')

        today_ts = calendar.timegm(
            datetime.today().utctimetuple())

        # Returns the german projects (parents) ids on typo3
        res = list()

        for project in self.browse(cr, uid, ids, context):
            project_desc_de = project.description_de.replace('\'', '\'\'')
            project_desc_fr = project.description_fr.replace('\'', '\'\'')
            if not project.country_id:
                project.update_informations()
                project = self.browse(cr, uid, project.id, context)

            # German description (parent)
            Sync_typo3.request_to_typo3(
                "insert into "
                "tx_drechildpoolmanagement_domain_model_projects"
                "(project_key, country, description,"
                "tstamp, crdate, l10n_parent) "
                "values ('{0}','{1}','{2}','{3}','{4}','{5}');".format(
                    project.code, project.country_id.name,
                    project_desc_de, today_ts,
                    today_ts, 0), 'upd')

            parent_id = self.get_project_from_typo3(
                cr, uid, project.code)
            res.append(parent_id)

            # French description
            Sync_typo3.request_to_typo3(
                "insert into "
                "tx_drechildpoolmanagement_domain_model_projects"
                "(project_key, country, description,"
                "tstamp, crdate, l10n_parent, sys_language_uid) "
                "values ('{0}','{1}','{2}','{3}','{4}','{5}',1);".format(
                    project.code, project.country_id.name,
                    project_desc_fr, today_ts,
                    today_ts, parent_id), 'upd')

            return res
