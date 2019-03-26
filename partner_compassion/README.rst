.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Upgrade Partners for Compassion Suisse
======================================

A. Upgrade Partners to Compassion Switzerland standards :
    - Add correspondance information
    - Redefines the views of the partners
    - Add partner geolocalization

B. E-mail tracking :
    - Post e-mails sent with Sendgrid in the partners
    - Track the reception of message inside the thread
    - Restrict e-mail followers

C. Add ambassador details information

Installation
============
1. The PostgreSQL extension pg_trgm should be available. In debian based distribution you have to install the postgresql-contrib module.
2. Install the pg_trgm extension to your database or give your postgresql user the SUPERUSER right (this allows the odoo module to install the extension to the database).

Configuration
=============
Add the following parameters to your Odoo configuration file:

* ``smb_user`` : user for connecting on the NAS of Compassion with Samba
* ``smb_pwd`` : password for Samba
* ``smb_ip`` : IP address of the NAS of Compassion
* ``smb_port`` : Samba port of the NAS
* ``partner_data_password`` : The password for encrypted ZIP file containing erased partner history

Add the following system parameters in Odoo->Settings->System Parameters

* ``partner_compassion.share_on_nas`` : Name of the Samba root share
* ``partner_compassion.store_path`` : Path to the ZIP file containing erased partner history

Known issues / Roadmap
======================

* Missing tests for mail_message and mail_thread

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
* Steve Ferry <steve_ferry@outlook.com>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
