# TODO JWT library
The library which is currently used seems to be abandoned : https://github.com/GehirnInc/python-jwt
(No update since Apr 19, 2022). It is not clear if this library is already a dependency of odoo.

Another possibility would be to switch to :
https://github.com/jpadilla/pyjwt



# TODO security properties
Describe what you can expect from this module in terms of security properties

# Security considerations

## Absence of method for token revocation

See https://stackoverflow.com/a/40385939 
TODO: should we support token revocation?

Attack:
The victim logs in through a shared machine to the translation platform.
They leave the machine and forget to log out.
The attacker extracts the JWT from the localStorage.
The attacker now has the same capabilities as the victim, and this token cannot be revoked.

## Indefinite validity of refresh_token
IMPL1: In the current implementation, if an attacker obtains a valid refresh token, they can keep getting fresh access_tokens indefinitely. This is because to obtain a pair (fresh_access_token, fresh_refresh_token), it is only necessary to provide a valid refresh_token. An attacker can thus continuously refresh their refresh_token to keep indefinite access. This is not good because there is no revocation mechanism.
IMPL2: alternate implementation: only refresh the access_token, not the refresh_token, so that the attacker loses access to the account after expiration of the refresh_token. To get a fresh refresh_token, it is necessary to login with (login, password, totp?)

Attack possible in IMPL1 and not IMPL2:
The victim logs in and their browser stores the refresh_token in the browser's storage.
The victim's computer is infected by malware and their (still valid) refresh_token is exfiltrated to the attacker's machine.
The attacker monitors all the victim's actions on odoo using the stolen access_token, refreshing the stolen refresh_token when necessary.
This can continue indefinitely in IMPL1 but not in IMPL2, as the refresh_token eventually expires.

# TODO Refresh tokens
https://www.rfc-editor.org/rfc/rfc6749#section-1.5
https://web.archive.org/web/20240930214312/https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/
https://web.archive.org/web/20240828080645/https://auth0.com/blog/securing-single-page-applications-with-refresh-token-rotation/

# Token design possibilities

## 0 : odoo session id in cookie
???

## 1 : simple access_token
After authentication, the user receives an access_token with a validity of 28 days.

### Pros
- Simple to implement, test, verify

### Cons
- No revocation mechanism
- long lived access_token (high impact vuln if XSS)
- cannot do Reuse detection

## 2 : access_token + refresh_token without revocation (current impl)
### Pros
- Already implemented
- No server state
- short lived access_token

### Cons
- refresh_token is essentially infinitely valid
- limited security benefit for case where Resource Server == Authorization Server
- *** refresh_token can be reused / replayed *** !!!

## 3 : access_token + Refresh Token Rotation with Reuse Detection
### Pros
- refresh_tokens cannot be reused / replayed
- refresh_tokens can be revoked upon logout

### Cons
- Need to keep state on the server -> mechanism for clearing DB periodically (cron)
