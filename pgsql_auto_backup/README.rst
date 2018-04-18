.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Database Auto-Backup
====================

The Database Auto-Backup module enables the user to make configurations for the automatic backup of the database. Backups can be taken on the local system or on a remote server, through SFTP.
You only have to specify the hostname, port, backup location and databasename (all will be pre-filled by default with correct data.
If you want to write to an external server with SFTP you will need to provide the IP, username and password for the remote backups.
The base of this module is taken from Odoo SA V6.1 (https://www.odoo.com/apps/modules/6.0/pgsql_auto_backup/) and then upgraded and heavily expanded.
This module is made and provided by VanRoey.be.

Automatic backup for all such configured databases can then be scheduled as follows:

1) Go to Settings / Technical / Automation / Scheduled actions.
2) Search the action 'Backup scheduler'.
3) Set it active and choose how often you wish to take backups.
4) If you want to write backups to a remote location you should fill in the SFTP details.

Credits
=======

Contributors
------------

* VanRoey.be - Yenthe Van Ginneken

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
