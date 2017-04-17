.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Sync spoken languages with GP
=============================
This module import all GP spoken languages from countries and partners
in odoo 8.0.
Spoken languages are iso 639-3

Partners spoken languages:
Select all spoken_langs with Partner CODEGA in GP (table langueparlee)
and import in odoo where partner_id is found

Countries spoken languages:
Select all spoken_langs with Country ISO3166 in GP (table langueparlee)
and import in odoo where country_id is found

All ids not found in odoo are displayed on a text field and stored in DB

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

	

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
* Emmanuel Mathier <emmanuel.mathier@gmail.com>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.