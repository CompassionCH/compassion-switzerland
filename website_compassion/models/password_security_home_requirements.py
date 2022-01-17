from odoo.addons.password_security.controllers.main import PasswordSecurityHome
from odoo.http import request


class PasswordSecurityHomeRequirements(PasswordSecurityHome):
    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        if qcontext.get('login'):
            user = request.env["res.users"].sudo().search([("login", "=", qcontext.get('login'))])
            message = user.password_match_message()
            lines = message.split("\r")
            message_HTML = ""
            start_ul = False
            for line in lines:
                if line[0:1] == "\n":
                    if not start_ul:
                        start_ul ^= True
                        message_HTML += "<ul>"
                    message_HTML += f"<li>{line[3:]}</li>"
                else:
                    if start_ul:
                        start_ul ^= True
                        message_HTML += "</ul>"
                    message_HTML += line + "<br>"
            qcontext["requirements"] = message_HTML
        return qcontext
