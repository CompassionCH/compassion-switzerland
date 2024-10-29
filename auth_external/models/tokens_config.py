from odoo import fields, models


class TokensConfig(models.Model):
    _name = "auth_external.tokens_config"
    _description = "Model used to configure the properties of issued tokens"

    issuer_id = fields.Char(
        required=True,
        help="""Identifier of the issuer of the token. This ensures we only
             accept tokens issued by ourself. This can for example be the
             company's domain name (e.g. example.com).""",
    )
    access_token_duration_hours = fields.Float(
        default=3.0,
        help="""Duration (in hours) for which the access token remains valid
             after issuance. Setting this value too low will cause too many
             refresh and strain the DB. Setting this value too high is a
             security risk as a stolen token can be used for longer. A
             reasonable value is a few hours (i.e. 3600 seconds or more).""",
    )

    refresh_token_duration_days = fields.Float(
        default=14.0,
        help="""Duration (in days) for which the refresh token remains valid
             after issuance. This define how many days the user can access the
             service without needing to re-authenticate, if they do not use the
             service and refresh their token in the mean time. For example, if
             this value is set to 10 and that a user uses their account every 9
             days (and thus refresh their tokens), they remain authenticated for
             ever. If at some point they do not refresh their tokens for 11
             days, they need to re-authenticate with their credentials (login,
             password, [totp])""",
    )

    def get_singleton(self) -> "TokensConfig":
        singleton = self.search([])
        singleton.ensure_one()
        return singleton

    _sql_constraints = [
        (
            "check_rt_longer_duration_than_at",
            "check(access_token_duration_hours < refresh_token_duration_days * 24)",
            "The refresh token must have longer duration than the access token.",
        ),
    ]
