from odoo import http
from odoo.http import request


class DonationRedirectController(http.Controller):
    @http.route("/donate", type="http", auth="public", website=True, sitemap=False)
    def redirect_donate(self, **kwargs):
        lang_code = request.lang.code  # get the language code
        if lang_code == "fr_CH":
            return request.redirect("https://compassion.ch/donner/")
        elif lang_code == "de_DE":
            return request.redirect("https://compassion.ch/spenden/")
        elif lang_code == "it_IT":
            return request.redirect("https://compassion.ch/donare/")
        else:
            return request.redirect("https://compassion.ch/spenden/")
