##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = 'res.users'

    connect_agent = fields.Boolean(
        string='Connect the Xivo agent after check_in ',
        default=True)

    @api.multi
    def asterisk_connect(self, log=True):
        for ast_user in self.filtered('connect_agent'):
            try:
                user, ast_server, ast_manager = \
                    self.env['asterisk.server'].sudo(
                        ast_user.id)._connect_to_asterisk()

                channel = '%s/%s' % (
                    ast_user.asterisk_chan_type, user.resource)

                _prefix = '*31' if log else '*32'
                extension = _prefix + ast_user.internal_number

                ast_manager.Originate(
                    channel,
                    context='default',
                    extension=extension,
                    priority=1,
                    timeout=str(ast_server.wait_time * 1000),
                    caller_id=ast_user.internal_number,
                    account=ast_user.cdraccount)
                message = "Your Xivo agent is now " \
                          f"{'connected' if log else 'disconnected'}."
                ast_user.notify_info(message)
                ast_manager.Logoff()
            except Exception as e:
                message = "Impossible to connect your Xivo agent\n"
                message += str(e)
                ast_user.notify_info(message)
