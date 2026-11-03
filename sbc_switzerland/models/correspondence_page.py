##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class CorrespondencePage(models.Model):
    _inherit = "correspondence.page"

    def fetch_image(self):
        """
        Use the original image of the page when the translated text is overlaid
        on it, instead of the final image which already contains another
        translation.
        """
        self.ensure_one()
        if self.correspondence_id._has_local_translation_overlay():
            if not self.original_page_image:
                self._compute_page_image("original")
            return self.original_page_image
        return super().fetch_image()
