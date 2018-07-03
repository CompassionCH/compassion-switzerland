.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Sponsor to beneficiary for Switzerland
======================================

This module tailors letters import for reading PDFs from the NAS.
It adds option to import letters with import configuration and option to select
multiple letters on import.

It also manage the Swiss translation platform for letters that need translation

Configuration
=============

WARNING: You must install detectlanguage library on your server. It's used to
detect language from a text.
https://github.com/detectlanguage/detectlanguage-python

pip install detectlanguage

Add the following parameters to your Odoo configuration file:

* ``detect_language_api_key`` : api key for use detectlanguage library
* ``smb_user`` : user for connecting on the NAS of Compassion with Samba
* ``smb_pwd`` : password for Samba
* ``smb_ip`` : IP address of the NAS of Compassion
* ``smb_port`` : Samba port of the NAS

Usage
=====

Used by the onramp_compassion module to send an email on reception of a new
child letter.

The letter is sent to the sponsor's email address, using a SendGrid email
template corresponding to the sponsor's language. Templates for every language
have to be registered in the TemplateList model after creating them on the
`SendGrid web interface <https://sendgrid.com/templates>`_.

The template should contain the following substitution variables which will be
replaced with corresponding values:

- ``{sponsor}`` Full name of the sponsor
- ``{child}`` First name of the child
- ``{letter_url}`` URL where the letter can be viewed/downloaded

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
* Stéphane Eicher <eicher31@hotmail.com>
* Michaël Sandoz <sandozmichael@hotmail.com>

Maintainer
----------

This module is maintained by
`Compassion Switzerland <https://www.compassion.ch>`_.
