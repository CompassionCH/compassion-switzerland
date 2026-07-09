from odoo import fields, models


class QualityTestVersion(models.Model):
    _name = "quality.test.version"
    _description = "Quality test version"

    test_id = fields.Many2one("quality.test", required=True, index=True)
    version = fields.Char(required=True)
    description = fields.Html(required=True)

    _sql_constraints = [
        (
            "unique_version",
            "UNIQUE (test_id, version)",
            "The version must be unique per quality test.",
        )
    ]
