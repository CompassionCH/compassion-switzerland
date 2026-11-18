The module needs a shared secret, used to verify that the requests it receives
really come from GitHub. Pick a random value, then:

1.  Add it to the `[options]` section of the Odoo configuration file and
    restart the server:

    ```bash
    github_webhook_secret = <YOUR SECRET>
    ```

2.  In the GitHub organisation, go to **Settings → Webhooks → Add webhook** and
    fill in:
    - **Payload URL**: `https://<your_domain>/github/webhook`
    - **Content type**: `application/json`. This is required, as the
      signature is computed on the raw body.
    - **Secret**: the value set in step 1.
    - **Events**: _Let me select individual events_, then **Pull requests**
      only.

GitHub sends a `ping` event as soon as the webhook is saved. A green tick in
the **Recent Deliveries** tab confirms that the whole chain works.
