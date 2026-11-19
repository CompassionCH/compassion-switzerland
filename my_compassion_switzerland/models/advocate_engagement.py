from odoo import fields, models


class AdvocateEngagement(models.Model):
    _inherit = "advocate.engagement"

    _order = "sequence, id"

    sequence = fields.Integer(
        default=10,
        help="Sequence of the engagement type, "
        "used to order the engagement types in the MyCompassion website",
    )

    activate_for_my_compassion = fields.Boolean(
        help="Publish the engagement type as an available "
        "engagement type on the MyCompassion website"
    )

    my_compassion_label = fields.Char(
        translate=True,
        help="Label used in MyCompassion website",
    )

    my_compassion_description = fields.Text(
        translate=True,
        help="Description of engagement type visible on the MyCompassion website",
    )

    my_compassion_image = fields.Image(
        max_width=1200,
        max_height=900,
        help="Image for the engagement type visible on the MyCompassion website",
    )

    my_compassion_alt_text = fields.Char(
        translate=True,
        help="Alt text for the image of the engagement type "
        "visible on the MyCompassion website",
    )

    my_compassion_external_link = fields.Char(
        help="External link for the engagement type which redirects "
        "from MyCompassion website to another website",
    )

    my_compassion_internal_link = fields.Char(
        help="Internal link for the engagement type which sends "
        "a request to the Odoo server",
    )

    my_compassion_thank_you_text = fields.Text(
        translate=True,
        help="Displayed thank you message to the volunteer if they "
        "are engaged in this engagement type",
    )
