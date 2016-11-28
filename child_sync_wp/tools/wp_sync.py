# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import csv
import shutil
import xmlrpclib
from xmlrpclib import Fault

import pysftp
import logging
from os import listdir, path, makedirs, remove

from wand.image import Image

from openerp import _
from openerp.exceptions import Warning
from openerp.tools import config

logger = logging.getLogger(__name__)


class WPSync(object):

    def __init__(self):
        host = config.get('wordpress_host')
        user = config.get('wordpress_user')
        password = config.get('wordpress_pwd')
        sftp_host = config.get('wp_sftp_host')
        sftp_user = config.get('wp_sftp_user')
        sftp_pw = config.get('wp_sftp_pwd')
        csv_path = config.get('wp_csv_path')
        pic_path = config.get('wp_pictures_path')
        if not (host and user and password and sftp_host and sftp_user and
                sftp_pw and pic_path):
            raise Warning(
                _("Missing Configuration"),
                _("Please add configuration for Wordpress uploads")
            )
        self.xmlrpc_server = xmlrpclib.ServerProxy(
            'http://' + host + '/xmlrpc.php')
        self.user = user
        self.pwd = password
        self.sftp = pysftp.Connection(sftp_host, sftp_user, password=sftp_pw)
        self.wp_csv_path = csv_path
        self.wp_pictures_path = pic_path

    def __del__(self):
        self.sftp.close()

    def test_xmlrpc(self):
        return self.xmlrpc_server.demo.sayHello()

    def upload_children(self, children):
        """ Push children to Wordpress website.

        1 - Create and upload a CSV file containing all children information
        2 - Upload all children pictures
        3 - Call XMLRPC method that will update Wordpress

        :param children: compassion.child recordset
        :return: result of xmlrpc call to wordpress (true/false)
        """
        logger.info("Child Upload on Wordpress started.")
        csv_file = self._construct_csv(children)
        logger.info(".... CSV file constructed : " + csv_file)
        with self.sftp.cd(self.wp_csv_path):
            self.sftp.put(csv_file)
        logger.info(".... CSV file uploaded.")
        remove(csv_file)

        pictures_folder = self._build_pictures(children)
        logger.info(".... Pictures generated.")
        with self.sftp.cd(self.wp_pictures_path):
            for picture_file in listdir(pictures_folder):
                self.sftp.put(pictures_folder + '/' + picture_file)
        logger.info(".... Pictures uploaded.")
        shutil.rmtree(pictures_folder, ignore_errors=True)

        result = self.xmlrpc_server.child_import.addChildren(
            self.user, self.pwd)
        if result:
            logger.info(
                "Child Upload on Wordpress finished: %s children imported "
                % len(result))
        else:
            logger.error("Child Upload failed." + str(result))
        return result

    def remove_children(self, children):
        try:
            res = self.xmlrpc_server.child_import.deleteChildren(
                self.user, self.pwd, children.mapped('local_id'))
            logger.info("Remove from Wordpress : " + str(res))
            return res
        except Fault:
            logger.error("Remove from Wordpress failed.")

        return False

    def remove_all_children(self):
        res = self.xmlrpc_server.child_import.deleteAllChildren(
            self.user, self.pwd)
        logger.info("Remove from Wordpress : " + str(res))
        return res

    def _construct_csv(self, children):
        """ Generates a CSV file for Wordpress children upload having the
        following structure :

        child_reference,firstname,fullname,birthday,gender,start_date,
        french_description,german_description,italian_description,
        country,french_project_description,german_project_description,
        italian_project_description

        :param children: compassion.child recordset
        :return: generated csv file path
        """
        temp_csv = 'child_upload.csv'
        with open(temp_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'child_reference', 'firstname', 'fullname', 'birthday',
                'gender', 'start_date', 'french_description',
                'german_description', 'italian_description', 'country',
                'french_project_description', 'german_project_description',
                'italian_project_description'
            ])
            for child in children:
                row = [
                    child.local_id, child.firstname, child.name,
                    child.birthdate, child.gender, child.unsponsored_since,
                    child.desc_fr, child.desc_de, child.desc_it,
                    child.project_id.country_id.name,
                    child.project_id.description_fr,
                    child.project_id.description_de,
                    child.project_id.description_it,
                ]
                writer.writerow(row)
        return temp_csv

    def _build_pictures(self, children):
        """
        Takes all fullshot of given children and put them in jpg files
        inside a temporary folder.
        :param children: compassion.child recordset
        :return: pictures path
        """
        child_directory = 'child_upload'
        if not path.exists(child_directory):
            makedirs(child_directory)
        for child in children:
            full_path = child_directory + '/' + child.local_id
            fullshot = full_path + '_f.jpg'
            headshot = full_path + '_h.jpg'
            with Image(blob=base64.b64decode(child.fullshot)) as pic:
                pic.save(filename=fullshot)
            with Image(blob=base64.b64decode(child.portrait)) as pic:
                pic.save(filename=headshot)
        return child_directory
