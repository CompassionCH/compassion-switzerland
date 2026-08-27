from odoo import fields, models


class QualityTestVersion(models.Model):
    _name = "quality.test.version"
    _description = "Quality test version"

    test_id = fields.Many2one("quality.test", required=True, index=True)
    version = fields.Char(required=True)
    step_ids = fields.One2many(
        "quality.test.step",
        "version_id",
        string="Test Steps",
        help="Procedure as it was when this version was activated.",
    )

    _sql_constraints = [
        (
            "unique_version",
            "UNIQUE (test_id, version)",
            "The version must be unique per quality test.",
        )
    ]
