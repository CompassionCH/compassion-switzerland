# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <cyril.sester@outlook.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging
from export_tools import export_tools
from openerp import models, _
from openerp.addons.l10n_ch_lsv_dd.wizard import export_utils

logger = logging.getLogger(__name__)


class post_dd_export_wizard(models.TransientModel):
    _inherit = 'post.dd.export.wizard'

    def _get_communications(self, line):
        return export_tools.get_communications(self, line)

    def _customize_records(self, records, properties):
        ''' We try to group lines if possible. '''
        grouped_lines = [records[0][1]]
        deb_account = records[1][1][72:81]
        ref = records[1][1][87:114]
        new_line = records[1][1]
        trans_id = 1
        nb_grouped = 1
        nb_transactions = 0

        for tuple in records[2:]:
            pay_line = tuple[0]
            line = tuple[1]
            if not pay_line:  # It's a header or total records
                # It's a total. We update trans_id and nb_transactions
                if line[35:37] == '97':
                    line = line[:37] + str(trans_id + 1).zfill(6) + \
                        line[43:53] + str(trans_id).zfill(6) + line[59:]
                    nb_transactions += trans_id
                    trans_id = 0
                grouped_lines.append(new_line)
                new_line = line
                deb_account = ''
                ref = ''
                continue
            if line[72:81] != deb_account or line[87:114] != ref:
                grouped_lines.append(new_line)
                trans_id += 1
                deb_account = line[72:81]
                ref = line[87:114]
                new_line = line
                new_line = new_line[:37] + \
                    str(trans_id).zfill(6) + new_line[43:]
                nb_grouped = 1
            else:
                nb_grouped += 1
                new_amount = float(
                    new_line[53:66]) / 100 + float(line[53:66]) / 100
                new_amount = self._format_number(new_amount, 13)
                new_com = export_utils.complete_line(
                    140, _('debit for %d period(s)') % nb_grouped)
                new_line = new_line[:53] + new_amount + \
                    new_line[66:402] + new_com + new_line[542:]

        grouped_lines.append(new_line)
        properties['nb_transactions'] = nb_transactions

        return grouped_lines
