Reconcile rules with bvr_ref of invoice for Compassion CH.

It finds a matching invoice for the move_line and reconciles only if the amount of the payment corresponds or if it is a multiple of the invoice amount. If many invoices are found, the first reconciled invoice is the current invoice (last invoice that is not in future). Then it reconciles the other invoices from last invoice to first.
