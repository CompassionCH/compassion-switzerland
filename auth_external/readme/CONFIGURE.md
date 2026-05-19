Please add a JWT signing key to your `odoo.conf` to keep external client sessions alive across server restarts. This module only issues JWTs for clients authenticating via the `/auth/*` endpoints (e.g. the translation-platform SPA), so regular Odoo web users are not affected. Without a configured key, the module generates a fresh ephemeral one at every startup, invalidating every issued JWT and forcing every external client user to re-login.

The key **must** be under the `[options]` section header. Odoo's config parser silently ignores keys outside of it:

```ini
[options]
auth_external.jwt_key = <your_secret_key>
```

If the key is missing or in the wrong section, you'll see this on startup (ERROR level), and the ephemeral key itself is logged at DEBUG level:

```
ERROR ... auth_external.jwt_key not configured under [options] in odoo.conf. Using an ephemeral key. [...]
```

## v18 notes

This module uses **PyJWT** (the `jwt` PyPI package by José Padilla), already shipped via Odoo core (`mail/tools/web_push.py` and the `server-auth` stack). No additional Python dependency declaration is needed in the manifest. The v14 module used the GehirnInc `jwt` package, which conflicts with PyJWT on the top-level `jwt` Python namespace and could not coexist.

JWT subject claims are stored as strings (RFC 7519 §4.1.2). PyJWT 2.x rejects integer subjects at decode time; the module coerces user ids to strings on encode and back to ints on verify.

The module also overrides `ir.http._dispatch` to stash the request's `Authorization` header in `threading.current_thread()`. v18's `borrow_request()` (used by `dispatch_rpc`) makes the request inaccessible from `res.users.check` / `_check_credentials` during XMLRPC calls; the thread-local survives `borrow_request` and lets the Bearer-token shortcut work for XMLRPC too.