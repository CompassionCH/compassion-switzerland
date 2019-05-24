The route is /postfinance/payment/<invoice_id> that can contain
following GET parameter for the payment:

* accept_url: the redirection url after successful payment
* decline_url: the redirection url after declined payment

The redirection page is /postfinance/payment/validate

If no accept_url and decline_url were passed, it will render the default confirmation page,
otherwise it will redirect the user accordingly.
