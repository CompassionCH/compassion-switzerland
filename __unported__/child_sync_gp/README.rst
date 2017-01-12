.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================
Sync Compassion Children with GP
================================

This module syncs all children and projects with GP so that the information
can be seen from GP.

Installation
============

Make sure you have pysmb installed (sudo pip install pysmb)

Configuration
=============

To configure this module, you need to add settings in .conf file of Odoo:

* mysql_host = <mysql host of gp>
* mysql_db = <mysql database of gp>
* mysql_user = <mysql user of gp>
* mysql_pw = <mysql password of gp>
* smb_user = <samba user for pushing child pictures on the NAS>
* smb_pwd = <samba password>
* smb_ip = <IP Address of the NAS>
* smb_port = <Samba Port>
* gp_pictures = <Path to the folder of child pictures on the NAS>

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.