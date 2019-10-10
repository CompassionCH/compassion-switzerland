# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) VanRoey.be - Yenthe Van Ginneken
#    Releasing children from poverty in Jesus' name
#    @author: VanRoey.be - Yenthe Van Ginneken
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import xmlrpclib
import socket
import requests
import os
import shutil
import functools
import time
import datetime
import re
import logging

from odoo import models, fields, api, tools, _
from odoo.exceptions import Warning as odooWarning

_logger = logging.getLogger(__name__)

try:
    import pysftp
except ImportError:
    _logger.error(
        'This module needs pysftp to automaticly write backups to the FTP '
        'through SFTP. Please install pysftp on your system. (sudo pip '
        'install pysftp)'
    )


def execute(connector, method, *args):
    try:
        res = getattr(connector, method)(*args)
    except socket.error, e:
        raise e
    return res


addons_path = tools.config['addons_path'] + '/pgsql_auto_backup/DBbackups'


class DbBackup(models.Model):
    _name = 'db.backup'

    @api.multi
    def get_db_list(self, host, port):
        uri = 'http://' + host + ':' + port
        conn = xmlrpclib.ServerProxy(uri + '/xmlrpc/db')
        db_list = execute(conn, 'list')
        return db_list

    @api.multi
    def _get_db_name(self):
        db_name = self._cr.dbname
        return db_name

    # Columns for local server configuration
    host = fields.Char('Host', size=100, required=True, default='localhost')
    port = fields.Char('Port', size=10, required=True, default=8069)
    name = fields.Char('Database', size=100, required=True,
                       help='Database you want to schedule backups for',
                       default=_get_db_name)
    folder = fields.Char('Backup Directory', size=100,
                         help='Absolute path for storing the backups',
                         required='True', default='/odoo/backups')
    backup_type = fields.Selection([('zip', 'Zip'), ('dump', 'Dump')],
                                   'Backup Type', required=True,
                                   default='dump')
    autoremove = fields.Boolean(
        'Auto. Remove Backups', help='If you check this option you can '
                                     'choose to automaticly remove the '
                                     'backup after xx days')
    days_to_keep = fields.Integer(
        'Remove after x days',
        help="Choose after how many days the backup should be deleted. For "
             "example:\nIf you fill in 5 the backups will be removed after "
             "5 days.",
        required=True)

    # Columns for external server (SFTP)
    sftp_write = fields.Boolean('Write to external server with sftp',
                                help="If you check this option you can "
                                     "specify the details needed to write to "
                                     "a remote server with SFTP.")
    sftp_path = fields.Char(
        'Path external server',
        help='The location to the folder where the dumps should be written '
             'to. For example /odoo/backups/.\nFiles will then be written to '
             '/odoo/backups/ on your remote server.')
    sftp_host = fields.Char('IP Address SFTP Server',
                            help='The IP address from your remote server. '
                                 'For example 192.168.0.1')
    sftp_port = fields.Integer(
        'SFTP Port',
        help='The port on the FTP server that accepts SSH/SFTP calls.',
        default=22)
    sftp_user = fields.Char(
        'Username SFTP Server',
        help='The username where the SFTP connection should be made with. '
             'This is the user on the external server.')
    sftp_password = fields.Char(
        'Password User SFTP Server',
        help='The password from the user where the SFTP connection should be '
             'made with. This is the password from the user on the external '
             'server.')
    days_to_keep_sftp = fields.Integer(
        'Remove SFTP after x days',
        help='Choose after how many days the backup should be deleted from the'
             ' FTP server. For example:\nIf you fill in 5 the backups will be '
             'removed after 5 days from the FTP server.', default=30)
    send_mail_sftp_fail = fields.Boolean(
        'Auto. E-mail on backup fail',
        help='If you check this option you can choose to automaticly get '
             'e-mailed when the backup to the external server failed.')
    email_to_notify = fields.Char(
        'E-mail to notify', help='Fill in the e-mail where you want to be '
                                 'notified that the backup failed on the FTP.'
    )

    @api.multi
    def _check_db_exist(self):
        self.ensure_one()

        db_list = self.get_db_list(self.host, self.port)
        if self.name in db_list:
            return True
        return False

    _constraints = [
        (_check_db_exist, _('Error ! No such database exists!'), [])]

    @api.multi
    def test_sftp_connection(self, context=None):
        self.ensure_one()

        # Check if there is a success or fail and write messages
        message_title = ""
        message_content = ""

        for rec in self:
            try:
                ip_host = rec.sftp_host
                post_host = rec.sftp_port
                username_login = rec.sftp_user
                password_login = rec.sftp_password
                # Connect with external server over SFTP, so we know sure that
                # everything works.
                srv = pysftp.Connection(
                    host=ip_host, username=username_login,
                    password=password_login, port=post_host)
                srv.close()
                # We have a success.
                message_title = "Connection Test Succeeded!"
                message_content = "Everything seems properly set up for " \
                                  "FTP back-ups!"
            except Exception, e:
                message_title = "Connection Test Failed!"
                if len(rec.sftp_host) < 8:
                    message_content += "\nYour IP address seems to be too " \
                                       "short.\n"
                message_content += "Here is what we got instead:\n"
        if "Failed" in message_title:
            raise odooWarning(_(message_title + '\n\n' +
                                message_content + "%s") % tools.ustr(e))
        else:
            raise odooWarning(_(message_title + '\n\n' + message_content))

    @api.multi
    def schedule_backup(self):
        conf_ids = self.search([])

        for rec in conf_ids:
            db_list = self.get_db_list(rec.host, rec.port)

            if rec.name in db_list:
                try:
                    if not os.path.isdir(rec.folder):
                        os.makedirs(rec.folder)
                except Exception:
                    raise
                # Create name for dumpfile.
                bkp_file = '%s_%s.%s' % (time.strftime(
                    '%d_%m_%Y_%H_%M_%S'), rec.name, rec.backup_type)
                file_path = os.path.join(rec.folder, bkp_file)
                uri = 'http://' + rec.host + ':' + rec.port
                try:
                    bkp_resp = requests.post(
                        uri + '/web/database/backup', stream=True,
                        data={
                            'master_pwd': tools.config['admin_passwd'],
                            'name': rec.name,
                            'backup_format': rec.backup_type
                        }
                    )
                    bkp_resp.raise_for_status()
                except Exception:
                    _logger.debug(
                        "Couldn't backup database %s. Bad database "
                        "administrator password for server running at "
                        "http://%s:%s" % (rec.name, rec.host, rec.port))
                    continue
                with open(file_path, 'wb') as fp:
                    # see https://github.com/kennethreitz/requests/issues/2155
                    bkp_resp.raw.read = functools.partial(
                        bkp_resp.raw.read, decode_content=True)
                    shutil.copyfileobj(bkp_resp.raw, fp)
            else:
                _logger.debug("database %s doesn't exist on http://%s:%s" %
                              (rec.name, rec.host, rec.port))

            # Check if user wants to write to SFTP or not.
            if rec.sftp_write is True:
                try:
                    # Store all values in variables
                    directory = rec.folder
                    path_to_write_to = rec.sftp_path
                    ip_host = rec.sftp_host
                    post_host = rec.sftp_port
                    username_login = rec.sftp_user
                    password_login = rec.sftp_password
                    # Connect with external server over SFTP
                    srv = pysftp.Connection(
                        host=ip_host, username=username_login,
                        password=password_login, port=post_host)
                    # set keepalive to prevent socket closed / connection
                    # dropped error
                    srv._transport.set_keepalive(30)
                    # Move to the correct directory on external server.
                    # If the user made a typo in his path with multiple
                    # slashes (/odoo//backups/) it will be fixed by this regex
                    path_to_write_to = re.sub('([/]{2,5})+', '/',
                                              path_to_write_to)
                    _logger.debug('sftp remote path: %s' % path_to_write_to)
                    try:
                        srv.chdir(path_to_write_to)
                    except IOError:
                        # Create directory and subdirs if they do not exist.
                        current_dir = ''
                        for dirElement in path_to_write_to.split('/'):
                            current_dir += dirElement + '/'
                            try:
                                srv.chdir(current_dir)
                            except:
                                _logger.info(
                                    '(Part of the) path didn\'t exist. '
                                    'Creating it now at ' + current_dir)
                                # Make directory and then navigate into it
                                srv.mkdir(current_dir, mode=777)
                                srv.chdir(current_dir)
                                pass
                    srv.chdir(path_to_write_to)
                    # Loop over all files in the directory.
                    for f in os.listdir(directory):
                        if rec.name in f:
                            fullpath = os.path.join(directory, f)
                            if os.path.isfile(fullpath):
                                if not srv.exists(f):
                                    _logger.info(
                                        'The file %s is not yet on the remote '
                                        'FTP Server ------ Copying file'
                                        % fullpath)
                                    srv.put(fullpath)
                                    _logger.info(
                                        'Copying File % s------ success'
                                        % fullpath)
                                else:
                                    _logger.debug(
                                        'File %s already exists on the remote '
                                        'FTP Server ------ skipped' % fullpath)

                    # Navigate in to the correct folder.
                    srv.chdir(path_to_write_to)

                    # Loop over all files in the directory from the back-ups.
                    # We will check the creation date of every back-up.
                    for file_in_dic in srv.listdir(path_to_write_to):
                        if rec.name in file_in_dic:
                            # Get the full path
                            fullpath = os.path.join(path_to_write_to,
                                                    file_in_dic)
                            # Get the timestamp from the file on the external
                            # server
                            timestamp = srv.stat(fullpath).st_atime
                            createtime = datetime.datetime.fromtimestamp(
                                timestamp)
                            now = datetime.datetime.now()
                            delta = now - createtime
                            # If the file is older than the days_to_keep_sftp
                            # (the days to keep that the user filled in on the
                            # Odoo form it will be removed.
                            if delta.days >= rec.days_to_keep_sftp:
                                # Only delete files, no directories!
                                if srv.isfile(fullpath) and (
                                        ".dump" in file_in_dic or
                                        '.zip' in file_in_dic):
                                    _logger.info(
                                        "Delete too old file from SFTP "
                                        "servers: " + file_in_dic)
                                    srv.unlink(file_in_dic)
                    # Close the SFTP session.
                    srv.close()
                except Exception, e:
                    _logger.debug(
                        'Exception! We couldn\'t back up to the FTP server..')
                    # At this point the SFTP backup failed. We will now check
                    # if the user wants
                    # an e-mail notification about this.
                    if rec.send_mail_sftp_fail:
                        # TODO This code is not working for version 10!
                        try:
                            ir_mail_server = self.pool.get('ir.mail_server')
                            message = "Dear,\n\nThe backup for the server " +\
                                      rec.host + " (IP: " + rec.sftp_host +\
                                      ") failed.Please check the following " \
                                      "details:\n\nIP address SFTP server: " +\
                                rec.sftp_host + "\nUsername: " + \
                                      rec.sftp_user + "\nPassword: " + \
                                rec.sftp_password + "\n\nError details: " + \
                                tools.ustr(e) + "\n\nWith kind regards"
                            msg = ir_mail_server.build_email(
                                "pgsql_auto_backup@" + rec.name + ".com",
                                [rec.email_to_notify],
                                "Backup from " + rec.host + "(" +
                                rec.sftp_host + ") failed", message)
                            ir_mail_server.send_email(self.env.cr,
                                                      self.env.user, msg)
                        except Exception:
                            pass

            # Remove all old files (on local server) in case this is
            # configured..
            if rec.autoremove:
                directory = rec.folder
                # Loop over all files in the directory.
                for f in os.listdir(directory):
                    fullpath = os.path.join(directory, f)
                    # Only delete the ones wich are from the current database
                    # (Makes it possible to save different databases in the
                    # same folder)
                    if rec.name in fullpath:
                        timestamp = os.stat(fullpath).st_ctime
                        createtime = datetime.datetime.fromtimestamp(
                            timestamp)
                        now = datetime.datetime.now()
                        delta = now - createtime
                        if delta.days >= rec.days_to_keep:
                            # Only delete files (which are .dump and .zip),
                            # no directories.
                            if os.path.isfile(fullpath) and (
                                    ".dump" in f or '.zip' in f):
                                _logger.info(
                                    "Delete local out-of-date file: " +
                                    fullpath)
                                os.remove(fullpath)
