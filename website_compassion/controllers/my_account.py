##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import locale

from odoo.http import request, route
from odoo.addons.cms_form_compassion.controllers.payment_controller import PaymentFormController


class MyAccountController(PaymentFormController):
    @route("/my", type="http", auth="user", website=True)
    def home(self, **kw):
        return request.redirect("/my/home")

    @route("/my/home", type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        return request.render("website_compassion.my_account_layout", {})

    @route("/my/children", type="http", auth="user", website=True)
    def my_children(self, **kwargs):
        partner = request.env.user.partner_id
        children = (partner.contracts_fully_managed +
                    partner.contracts_correspondant +
                    partner.contracts_paid)\
            .mapped("child_id").sorted("preferred_name")
        if len(children) == 0:
            return request.render(
                "website_compassion.my_children_empty_page_content", {}
            )
        else:
            return request.redirect(f"/my/child/{children[0].id}")

    @route("/my/child/<int:child_id>", type="http", auth="user", website=True)
    def my_child(self, child_id, **kwargs):
        # Modify locale so that dates are printed in correct language
        locale.setlocale(locale.LC_TIME, request.env.context['lang'] + '.utf8')

        partner = request.env.user.partner_id
        children = (partner.contracts_fully_managed +
                    partner.contracts_correspondant +
                    partner.contracts_paid) \
            .mapped("child_id").sorted("preferred_name")
        child_id = children.filtered(lambda child: child.id == child_id)
        if not child_id:
            return request.redirect(f"/my/children")
        else:
            child_id.get_infos()
            return request.render(
                "website_compassion.my_children_page_template",
                {"child_id": child_id},
            )
