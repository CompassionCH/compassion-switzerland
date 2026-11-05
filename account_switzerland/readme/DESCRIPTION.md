Accounting customizations for Compassion Switzerland.

**Background import of EBICS files**

This module speeds up the processing of EBICS files with the OCA bank
statement import modules.

When an EBICS file is processed, `account_ebics` splits it into one
CAMT file per bank account statement. Instead of importing all of them
in the same transaction, this module imports each statement in a
separate background job (using `with_delay_sh` from `queue_job_optional`).

Each job imports its statement, links it to the EBICS file and appends
the import results to the processing notes of the EBICS file.

**Labels of payment order journal items**

By default, Odoo labels the journal items of a payment with the payment
method and the memo (for payment orders, the order name). For payments
generated from a payment order, this module uses the payment reference
instead, which holds the communications of the payment lines. This
restores the behaviour of Odoo 14 and eases the reconciliation of the
journal items, for instance with direct debit returns.

**Split a journal entry in two**

A wizard, available from the "Split Entry" button of any journal entry
(invoice, bill, miscellaneous entry, ... in any state and payment state),
splits the journal items of an entry between the current entry and a copy.
For each item, the user chooses to keep it, move it to the new entry, split
it proportionally (tax items) or use it as a total item (for instance the
receivable or payable item), which is shared so that both entries stay
balanced. The reconciliations of the total items are shared as well, and the
new entry gets the same state as the original one.
