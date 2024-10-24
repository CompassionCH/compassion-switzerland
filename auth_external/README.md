# Compassion CH External Auth
This module is intended to allow authentication and authorization to the odoo backend from various frontends (the first use-case is for the translation platform, https://github.com/CompassionCH/translation-platform-web).
This custom module was required for the following reasons:
1. Odoo xmlrpc calls required to provide the (login, password) pair for each call, which required the storage in the user's browser. This would be a very important security risk, for example if an XSS vulnerability was discovered in the frontend.
2. Odoo xmlrpc calls do not support users who enabled 2FA. 

For these reasons, this module was developped.

A typical user session plays out as follows:
1. The user makes a request to `/auth/login`, providing their credentials (`login`, `password`, optionally `totp`). If the credentials are verified (using the `auth_totp` module if the user activated 2FA), the server returns an object which includes (not exhaustive) :
    - A JWT `access_token` which will be used to authorize the following xmlrpc requests. This token contains a Message Authentication Code produced using the `access_token_signing_key`, which allows to verify the authenticity of this token (without keeping state on the server for each token). This token remains valid a few hours (configurable through `auth_external.tokens_config`).
    - A JWT `refresh_token` which will be used to refresh the `access_token` (and also the `refresh_token`). This is described below. This token remains valid a few days/weeks. This duration of validity determines the maximum period during which a user can not use the application and still remain "connected". If the user regularly uses the application, the tokens are refreshed and they could remain "connected" indefinetly without needing to re-submit their credentials.
2. The user uses their `access_token` to make xmlrpc requests to the odoo backend.
3. The user refreshes their tokens by making a request to `/auth/refresh`, providing their current `refresh_token`. If the `refresh_token` is considered valid (authentic, non-expired, non-revoked), a fresh (`access_token`, `refresh_token`) pair is returned, and the provided `refresh_token` is revoked. 
4. When the user is done using the platform, they make a request to `/auth/logout`, providing their current `refresh_token`. This revokes all `refresh_token`s of the family (the original one obtained during login and the subsequent ones obtained through refreshes).

To get a more precise idea of how to use this module, have a look at `tests/test_auth_controller.py:test_full_2fa_user_lifecycle`.

# Security 
## Refresh Token Reuse Detection (RTRD) mechanism
This feature is heavily inspired by this article: https://web.archive.org/web/20240828080645/https://auth0.com/blog/securing-single-page-applications-with-refresh-token-rotation/#Automatic-Reuse-Detection

It prevents reuse of `refresh_token`s by keeping a list of the issued `refresh_token`s (see `models/refresh_tokens.py`). 
The tokens are stored as a doubly linked list, the parent `refresh_token` being linked to a child `refresh_token` after the former was used to authorize the issuance of the latter.
Once a token is used to authorize a refresh, it is marked as revoked.
If a revoked token is submitted, it means that it was probably intercepted/exfiltrated by a malicious actor. In this case, we revoke all tokens of the token family, and the user has to submit their credentials again (through `/auth/login`) in order to use the platform again.

## Tests
`tests/test_auth_controller.py` contains multiple unit tests which assert the security properties of this module. For example, `test_access_denied_2fa_correct_password_incorrect_totp` verifies that the login fails if a user with 2FA enabled tries to login with a correct password but an incorrect TOTP code.



# TODO 
## JWT library
The library which is currently used seems to be abandoned : https://github.com/GehirnInc/python-jwt
(No update since Apr 19, 2022). It is not clear if this library is already a dependency of odoo.

Another possibility would be to switch to :
https://github.com/jpadilla/pyjwt




# References
Refresh tokens in OAuth 2.0: https://www.rfc-editor.org/rfc/rfc6749#section-1.5
https://web.archive.org/web/20240930214312/https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/
https://web.archive.org/web/20240828080645/https://auth0.com/blog/securing-single-page-applications-with-refresh-token-rotation/

