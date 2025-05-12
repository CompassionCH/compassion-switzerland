Tokens in secure cookies
------------------------

Currently, tokens are stored in the localStorage in the frontend. This is dangerous if the frontend contains an XSS vulnerability (token extraction).
We should use Secure, HttpOnly, Strict=..., Domain=..., Path=...

https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#cookies
https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#security

In the process of trying to store the tokens in HttpOnly cookies, I discovered that the XmlRpcClient library used by the frontend (`import { XmlRpcClient } from '@foxglove/xmlrpc';`) does not support the withCredentials property (https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/withCredentials). This means that the access token cookie is not being sent with XmlRpc requests, and thus the server rejects them with AccessDenied. It would require substantial efforts to use another library or to re-implement the library with the required withCredentials property, so currently, the tokens remain stored in localStorage. This presents an important security vulnerability if an XSS vulnerability is discovered in the frontend. In that case, the tokens can be extracted by an attacker and used to make xmlrpc requests for the account of the victim. Significant care should thus be invested in testing the frontend for XSS vulnerabilities.

JWT library
-----------

The library which is currently used seems to be abandoned : https://github.com/GehirnInc/python-jwt
(No update since Apr 19, 2022). It is not clear if this library is already a dependency of odoo.

Another possibility would be to switch to :
https://github.com/jpadilla/pyjwt