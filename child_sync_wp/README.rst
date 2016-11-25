.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Push children on Wordpress website
==================================
Use XML-RPC Connector to Wordpress website

Installation
============
You need to have python wand and pysftp installed.

Configuration
=============
Add the following parameters to your Odoo configuration file:

* ``wordpress_host`` : the server url of your wordpress installation (ex: wp.localhost.com)
* ``wordpress_user`` : a wordpress user which have read/write access to the childpool
* ``wordpress_pwd`` : the password of the wordpress user
* ``wp_sftp_host`` : the server url of your wordpress sftp (ex: wp.localhost.com)
* ``wp_sftp_user`` : a sftp user of your wordpress server
* ``wp_sftp_pwd`` : the sftp password
* ``wp_csv_path`` : file location on the remote wp where to put the csv of children
* ``wp_pictures_path`` : remote path for the child pictures

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.