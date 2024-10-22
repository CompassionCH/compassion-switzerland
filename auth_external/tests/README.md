# Running the tests
```sh
odoo/odoo-bin -c etc/dev_t1486.conf -u auth_external -i auth_external --test-tags=auth_external --stop-after-init
```

# TODO : Revokable refresh_tokens
- you can only submit a valid refresh_token for revocation
- you cannot refresh using a revoked refresh_token
- 

# TODO : Automatic reuse detection
- If a refresh token is reused, the whole token family is revoked
