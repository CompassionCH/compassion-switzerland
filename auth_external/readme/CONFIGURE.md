Please add a JWT token in your odoo.conf in order to allow reconnection of users accross server restarts. If you don't have any, you will see a new key generated in the DEBUG logs.

```auth_external.jwt_key = <your_secret_key>```

## v18 notes

This module uses **PyJWT** (the `jwt` PyPI package by José Padilla), already shipped via Odoo core (`mail/tools/web_push.py` and the `server-auth` stack). No additional Python dependency declaration is needed in the manifest. The v14 module used the GehirnInc `jwt` package, which conflicts with PyJWT on the top-level `jwt` Python namespace and could not coexist.

JWT subject claims are stored as strings (RFC 7519 §4.1.2). PyJWT 2.x rejects integer subjects at decode time; the module coerces user ids to strings on encode and back to ints on verify.

The module also overrides `ir.http._dispatch` to stash the request's `Authorization` header in `threading.current_thread()`. v18's `borrow_request()` (used by `dispatch_rpc`) makes the request inaccessible from `res.users.check` / `_check_credentials` during XMLRPC calls; the thread-local survives `borrow_request` and lets the Bearer-token shortcut work for XMLRPC too.