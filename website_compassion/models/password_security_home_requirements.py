from odoo.addons.password_security.controllers.main import PasswordSecurityHome
from odoo.http import request


class PasswordSecurityHomeRequirements(PasswordSecurityHome):
    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        if qcontext.get('login'):
            user = request.env["res.users"].sudo().search([("login", "=", qcontext.get('login'))])
            message = user.password_match_message()
            lines = message.split("\n")
            message_html = ""
            start_ul = False
            for line in lines:
                if line[0:1] == "*":
                    if not start_ul:
                        start_ul ^= True
                        message_html += "<ul>"
                    message_html += f"<li>{line[2:]}</li>"
                else:
                    if start_ul:
                        start_ul ^= True
                        message_html += "</ul>"
                    message_html += line + "<br>"
            qcontext["requirements"] = message_html
        return qcontext
