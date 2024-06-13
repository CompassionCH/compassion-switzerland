Your Mandrill account must be configured in order to receive mail events
via webhooks.

1.  Launch Odoo with the newly installed module
2.  Open the Mandrill web interface and select new webhook under the
    setting tab
3.  Select the list of events you want to be notified about and set the
    url as follows

``` html
https://<your_domain>/mail/tracking/mandrill/<your_database>
```

If Mandrill displays an error it might be because it wasn't able to
reach your url. Make sure that your server is running and that the path
to your route has been setup correctly.

Once the webhook has been successfully created on the Mandrill interface
it will receive a webhook key. This key is used to validate Mandrill
request to your server and avoid undesired request from third party.
More info on [Mandrill's
documentation](https://mailchimp.com/developer/transactional/guides/track-respond-activity-webhooks/#authenticating-webhook-requests).

To enable the validation process copy the key you've found on Mandrill's
interface in your Odoo configuration file with the name
mandrill_webhook_key.

``` bash
mandrill_webhook_key = <YOUR KEY>
```

If you choose **not** to specify the webhook key in your configuration
file the route will still be accessible by Mandrill. **But use caution
as anyone with your url could trigger your route.**
