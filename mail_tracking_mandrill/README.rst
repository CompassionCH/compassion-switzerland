.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

======================
Mandrill Mail Tracking
======================

This module integrates
`Mandrill <https://mailchimp.com/features/transactional-email/>`_ (now known as Transactional-Email) with Odoo.
E-mails sent through Mandrill will be tracked using Mandrill Webhook Events.

Installation
============
In its current version the module does not support multi-database installation.

The module only dependency is `mail_tracking`.

No external python library are required.

Configuration
=============

Your Mandrill account must be configured in order to receive mail events via webhooks.

1. Launch Odoo with the newly installed module
2. Open the Mandrill web interface and select `new webhook` under the `setting` tab
3. Select the list of events you want to be notified about and set the url as follows

.. code:: html

    https://<your_domain>/mail/tracking/mandrill/<your_database>

If Mandrill displays an error it might be because it wasn't able to reach your url. Make sure
that your server is running and that the path to your route has been setup correctly.

Once the webhook has been successfully created on the Mandrill interface it will receive a `webhook key`.
This key is used to validate Mandrill request to your server and avoid undesired request from third party.
More info on `Mandrill's documentation <https://mailchimp.com/developer/transactional/guides/track-respond-activity-webhooks/#authenticating-webhook-requests>`_.

To enable the validation process copy the key you've found on Mandrill's interface
in your Odoo configuration file with the name `mandrill_webhook_key`.

.. code:: bash

    mandrill_webhook_key = <YOUR KEY>

If you choose **not** to specify the webhook key in your configuration file the route will
still be accessible by Mandrill. **But use caution as anyone with your url could trigger your route.**

Usage
=====

Once configured changes are invisible for the backend user. No views have been added or modified.
This module relies only on already existing ( trough `mail_tracking`) model `mail_tracking_email`.
The appropriated process function will be triggered when an event from Mandrill is received.

Known issues / Roadmap
======================


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/social/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Mandrill logo: `SVG Icon <https://seeklogo.com/vector-logo/273632/mandrill>`_.

Contributors
------------
* Jonathan Guerne <guernej@compassion.ch>

This work was mainly based on multiple other SMTP service integration in Odoo

* `Mandrill mail events integration by Antiun Ingeniería S.L., Odoo Community Association (OCA) <https://apps.odoo.com/apps/modules/8.0/mail_mandrill/>`_
* `Mail tracking for Mailgun by  Tecnativa , Odoo Community Association (OCA) <https://apps.odoo.com/apps/modules/12.0/mail_tracking_mailgun/>`_
* `SendGrid by  Compassion CH , Odoo Community Association (OCA) <https://apps.odoo.com/apps/modules/10.0/mail_sendgrid/>`_

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
