.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Account bank statement reconcile Compassion
===========================================

Reconcile rules with bvr_ref of invoice for Compassion CH.

It finds a matching invoice for the move_line and reconciles only if the
amount of the payment corresponds or if it is a multiple of the invoice
amount. If many invoices are found, the first reconciled invoice is the
current invoice (last invoice that is not in future).
Then it reconciles the other invoices from last invoice to first.

Usage
=====

To use this module, you need to:

* Go to Accounting -> Bank Statement -> Reconcile

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.