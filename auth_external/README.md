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