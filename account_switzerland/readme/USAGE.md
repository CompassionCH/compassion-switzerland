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

**Split a journal entry in two**

Open a journal entry and click on *Split Entry*. For each journal item,
choose the action:

- *Keep*: the item stays in the current entry.
- *Move to the new entry*: the item goes to the new entry (a copy of the
  current one).
- *Split (taxes)*: a tax item is shared between both entries in proportion
  to the base items that are moved (default for tax items).
- *Total (adapt and split)*: the item (default for the receivable or payable
  item of an invoice) is shared between both entries so that each one is
  balanced. Existing reconciliations and payments are redistributed on the
  two items, starting with the current entry.

Then click on *Split*. The new entry is posted, draft or cancelled like the
original one. At least one item must be moved and one kept. Entries that
are hashed or in a locked period, tax items that are reconciled, and
reconciliations with exchange difference or cash basis entries cannot be
split. The items linked to a payment or a bank statement must be kept.
