Please add a JWT token in your odoo.conf in order to allow reconnection of users accross server restarts. If you don't have any, you will see a new key generated in the DEBUG logs.

```auth_external.jwt_key = <your_secret_key>```