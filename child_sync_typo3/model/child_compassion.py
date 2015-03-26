# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import sys
import json
import calendar
import base64

from openerp.osv import orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from sync_typo3 import Sync_typo3
from datetime import datetime, timedelta


class compassion_child(orm.Model):
    _inherit = 'compassion.child'

    def _get_typo3_child_id(self, cr, uid, child_code):
        res_query = Sync_typo3.request_to_typo3(
            "select * "
            "from tx_drechildpoolmanagement_domain_model_children "
            "where child_key='%s';" % child_code, 'sel')
        res = 0
        try:
            res = json.loads(res_query)[0]['uid']
        except:
            raise orm.except_orm(
                _('Typo3 Error'),
                _('Child %s not found on typo3') % child_code)

        return res

    def child_add_to_typo3(self, cr, uid, ids, context=None):
        self._recompute_unsponsored(cr, uid, ids, context)

        # Solve the encoding problems on child's descriptions
        reload(sys)
        sys.setdefaultencoding('UTF8')

        for child in self.browse(cr, uid, ids, context):
            project_obj = self.pool.get('compassion.project')
            project = project_obj.get_project_from_typo3(
                cr, uid, child.project_id.code)

            if not project:
                project = project_obj.project_add_to_typo3(
                    cr, uid, [child.project_id.id], context)[0]

            child_gender = self._get_gender(cr, uid, child.gender, context)
            child_image = child.code + "_f.jpg," + child.code + "_h.jpg"

            today_ts = calendar.timegm(
                datetime.today().utctimetuple())
            consign_ts = timedelta(days=200).total_seconds()
            if child.birthdate:
                child_birth_date = calendar.timegm(
                    datetime.strptime(child.birthdate, DF).utctimetuple())
            else:
                child_birth_date = 0
            if child.unsponsored_since:
                child_unsponsored_date = calendar.timegm(
                    datetime.strptime(child.unsponsored_since,
                                      DF).utctimetuple())
            else:
                child_unsponsored_date = today_ts

            # Fix ' in description
            child_desc_de = child.desc_de.replace('\'', '\'\'')
            child_desc_fr = child.desc_fr.replace('\'', '\'\'')

            # German description (parent)
            Sync_typo3.request_to_typo3(
                "insert into "
                "tx_drechildpoolmanagement_domain_model_children"
                "(child_key, child_name_full, child_name_personal,"
                " child_gender, child_biography,"
                " consignment_date, tstamp, crdate, consignment_expiry_date,"
                " l10n_parent,image,child_birth_date,"
                " child_unsponsored_since_date,project) "
                "values ('{0}','{1}','{2}','{3}','{4}','{5}',"
                "        '{6}','{7}','{8}','{9}','{10}','{11}',"
                "        '{12}',{13});".format(
                    child.code, child.name, child.firstname,
                    child_gender, child_desc_de,
                    today_ts, today_ts, today_ts, today_ts + consign_ts,
                    0, child_image, child_birth_date, child_unsponsored_date,
                    project), 'upd')

            parent_id = self._get_typo3_child_id(cr, uid, child.code)

            # French description
            query = "insert into " \
                "tx_drechildpoolmanagement_domain_model_children" \
                "(child_key,child_name_full,child_name_personal," \
                " child_gender,child_biography,consignment_date,tstamp," \
                " crdate,consignment_expiry_date,l10n_parent,image," \
                " child_birth_date,child_unsponsored_since_date," \
                " project,sys_language_uid) " \
                "values ('{0}','{1}','{2}','{3}','{4}','{5}','{6}'," \
                "        '{7}','{8}','{9}','{10}'," \
                "        '{11}','{12}',{13},1);".format(
                    child.code, child.name, child.firstname,
                    child_gender, child_desc_fr,
                    today_ts, today_ts, today_ts, today_ts + consign_ts,
                    parent_id, child_image, child_birth_date,
                    child_unsponsored_date, project)

            # Assign child to childpool
            max_sorting = int(json.loads(Sync_typo3.request_to_typo3(
                "select max(sorting) as max from "
                "tx_drechildpoolmanagement_childpools_children_mm",
                'sel'))[0]['max'])
            query += "insert into " \
                "tx_drechildpoolmanagement_childpools_children_mm" \
                "(uid_foreign,sorting) " \
                "values ({0},{1})".format(parent_id, max_sorting)

            Sync_typo3.request_to_typo3(query, 'upd')

        self._add_child_pictures_to_typo3(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'I'})
        return Sync_typo3.sync_typo3_index()

    def child_remove_from_typo3(self, cr, uid, ids, context=None):
        child_codes = list()

        for child in self.browse(cr, uid, ids, context):
            child_uid = self._get_typo3_child_id(cr, uid, child.code)
            Sync_typo3.request_to_typo3(
                "delete from tx_drechildpoolmanagement_childpools_children_mm"
                " where uid_foreign={0};"
                "delete from tx_drechildpoolmanagement_domain_model_children "
                "where child_key='{1}';".format(child_uid, child.code), 'upd')
            state = 'R' if child.has_been_sponsored else 'N'
            child.write({'state': state})
            child_codes.append(child.code)

        Sync_typo3.delete_child_photos(child_codes)
        return Sync_typo3.sync_typo3_index()

    def _add_child_pictures_to_typo3(self, cr, uid, ids, context=None):
        for child in self.browse(cr, uid, ids, context):

            head_image = child.code + "_h.jpg"
            full_image = child.code + "_f.jpg"

            file_head = open(head_image, "wb")
            file_head.write(base64.b64decode(child.portrait))
            file_head.close()

            file_fullshot = open(full_image, "wb")
            file_fullshot.write(base64.b64decode(child.fullshot))
            file_fullshot.close()

            Sync_typo3.add_child_photos(head_image, full_image)

    def child_sponsored(self, cr, uid, ids, context=None):
        res = super(compassion_child, self).child_sponsored(
            self, cr, uid, ids, context)

        """ Remove children from the website when they are sponsored. """
        to_remove_from_web = []
        for child in self.browse(cr, uid, ids, context):
            if child.state == 'I':
                to_remove_from_web.append(child.id)
        if to_remove_from_web:
            self.child_remove_from_typo3(cr, uid, to_remove_from_web,
                                         context)
        return res
