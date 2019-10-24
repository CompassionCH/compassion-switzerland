.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

OpenERP MySQL Connector
=======================

Utility module that enables other modules that depends on it to access a
MySQL server that is defined a settings screen.


Installation
============

To install this module, you need to install dependencies:

* requires python-MySQLdb to be installed on the server.

Configuration
=============

To configure this module, you need to add settings in .conf file of Odoo:

* mysql_host = <mysql host>
* mysql_db = <mysql database>
* mysql_user = <mysql user>
* mysql_pw = <mysql password>

Usage
=====

You can use this module directly from code:

* from mysql_connector.model.mysql_connector import mysql_connector
* con = mysql_connector()
* res_query = mysql_connector.select_all(sql, args)
* mysql_connector.upsert(table, vals)

See file mysql_connector.py for all supported methods. You can as well
inherit to expand the functionalities.

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
