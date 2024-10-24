
# TODO add access rules
2024-10-22 14:03:51,077 62965 WARNING t1486 odoo.modules.loading: The model auth_external.refresh_token has no access rules, consider adding one. E.g. access_auth_external_refresh_token,access_auth_external_refresh_token,model_auth_external_refresh_token,base.group_user,1,0,0,0 


# TODO JWT library
The library which is currently used seems to be abandoned : https://github.com/GehirnInc/python-jwt
(No update since Apr 19, 2022). It is not clear if this library is already a dependency of odoo.

Another possibility would be to switch to :
https://github.com/jpadilla/pyjwt



# TODO security properties
Describe what you can expect from this module in terms of security properties

# Security considerations

# Refresh tokens
https://www.rfc-editor.org/rfc/rfc6749#section-1.5
https://web.archive.org/web/20240930214312/https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/
https://web.archive.org/web/20240828080645/https://auth0.com/blog/securing-single-page-applications-with-refresh-token-rotation/

