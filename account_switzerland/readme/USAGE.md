**Background import of EBICS files**

Process an EBICS file (CAMT.052, CAMT.053 or CAMT.054) as usual. The
processing notes indicate that the statements are imported in background
jobs. Follow their progress in the queue jobs; once done, the imported
statements are listed on the EBICS file.

**Labels of payment order journal items**

Confirm a payment order (for instance a direct debit order) and mark it
as uploaded. The journal items of the generated payments are labelled
with the communications of their payment lines. Payments without a
payment reference, and payments not linked to a payment order, keep the
default Odoo label.
