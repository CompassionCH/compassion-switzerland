##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.error import HTTPError

from .auto_texts import CHRISTMAS_TEXTS

import base64
from datetime import datetime, timedelta
from base64 import b64decode, b64encode
from os import path, remove
from urllib.parse import urlparse, urlencode
from zipfile import ZipFile
from urllib.request import urlretrieve, urlopen
from math import ceil
import secrets
from passlib.context import CryptContext

from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

from odoo import fields, _
from odoo.http import request, route, local_redirect
from odoo.addons.web.controllers.main import content_disposition
from odoo.addons.cms_form_compassion.controllers.payment_controller import (
    PaymentFormController,
)

from ..tools.image_compression import compress_big_images

IMG_URL = "https://erp.compassion.ch/web/image/compassion.child.pictures/{id}/fullshot/"


def _get_user_children(state=None):
    """
    Find all the children for which the connected user has a contract for.
    There is the possibility to fetch either only active children or only those
    that are terminated / cancelled. By default, all sponsorships are returned

    :return: a recordset of child.compassion which the connected user sponsors
    """
    env = request.env
    partner = env.user.partner_id
    end_reason_child_depart = env.ref("sponsorship_compassion.end_reason_depart")

    def filter_sponsorships(sponsorship):
        can_show = True
        is_active = sponsorship.state not in ["draft", "cancelled", "terminated"]
        is_recent_terminated = (
                sponsorship.state == "terminated"
                and sponsorship.can_write_letter
                and sponsorship.end_reason_id == end_reason_child_depart
        )
        exit_communication_sent = (
                sponsorship.state == "terminated"
                and sponsorship.sds_state != "sub_waiting"
        )

        if state == "active":
            can_show = (
                is_active or is_recent_terminated
                and not exit_communication_sent
            )
        elif state == "terminated":
            can_show = (
                sponsorship.state == "terminated"
                and not is_recent_terminated or exit_communication_sent
            )
        elif state == "write":
            can_show = sponsorship.can_write_letter

        return can_show

    return partner.get_portal_sponsorships().with_context(
        allow_during_suspension=True).filtered(filter_sponsorships).mapped(
        "child_id").sorted("preferred_name")


def _fetch_images_from_child(child):
    """
    Pass through the pictures of the child given as parameter and fills up a
    list of tuples of the form (image, full_path). Here, image is a record and
    full_path is the complete path of the image in the future archive.
    :param child: the child for which we want to create the image list
    :return: a list of tuples of the form (image, full_path)
    """
    images = []
    for image in child.pictures_ids:
        ext = image.image_url.split(".")[-1]
        filename = f"{child.preferred_name}_" \
                   f"{image.date}_{child.local_id}.{ext}"
        folder = f"{child.preferred_name}_{child.local_id}"
        full_path = path.join(folder, filename)
        images.append((image, full_path))
    return images


def _create_archive(images, archive_name):
    """
    Create an archive from a list of images and the name of the future archive.
    Some files are created locally but are deleted after they are used by the
    method.
    :param images: a list of tuples of the form [(image1, full_path1), ...]
    :param archive_name: the name of the future archive
    :return: a response for the client to download the created archive
    """
    with ZipFile(archive_name, "w") as archive:
        for (img, full_path) in images:
            filename = path.basename(full_path)

            # Create file, write to archive and delete it from os
            img_url = IMG_URL.format(id=img.id)
            try:
                urlretrieve(img_url, filename)
            except HTTPError:
                continue
            archive.write(filename, full_path)
            remove(filename)

    # Get binary content of the archive, then delete the latter
    with open(archive_name, "rb") as archive:
        zip_data = archive.read()
    remove(archive_name)

    return request.make_response(
        zip_data,
        [("Content-Type", "application/zip"),
         ("Content-Disposition", content_disposition(archive_name))]
    )


def _single_image_response(image):
    ext = image.image_url.split(".")[-1]
    data = urlopen(IMG_URL.format(id=image.id)).read()
    filename = f"{image.child_id.preferred_name}_{image.date}.{ext}"

    return request.make_response(
        data,
        [("Content-Type", f"image/{ext}"),
         ("Content-Disposition", content_disposition(filename))]
    )


def _download_image(child_id, obj_id):
    """
    Download one or multiple images (in a .zip archive if more than one) and
    return a response for the user to download it.
    :param type: the type of download, either 'single', 'multiple' or 'all'
    :param obj_id: the id of the image to download or None
    :param child_id: the id of the child to download from or None
    :return: A response for the user to download a single image or an archive
    containing multiples
    """
    # All children, all images
    if child_id < 0 and obj_id < 0:
        images = []
        for child in _get_user_children():
            images += _fetch_images_from_child(child)
        filename = f"my_children_pictures.zip"
        return _create_archive(images, filename)

    if child_id < 0:
        return False

    # One child
    child = request.env["compassion.child"].browse(child_id)

    # All images from a child
    if child and obj_id < 0:
        images = _fetch_images_from_child(child)
        filename = f"{child.preferred_name}_{child.local_id}.zip"
        return _create_archive(images, filename)

    # A single image from a child
    if child and obj_id > 0:
        image = child.pictures_ids.filtered(lambda p: p.id == obj_id)
        return _single_image_response(image)

    return False


class MyAccountController(PaymentFormController):
    @route("/my/login/<partner_uuid>/<redirect_page>", type="http", auth="public",
           website=True)
    def magic_login(self, partner_uuid=None, redirect_page=None, **kwargs):
        if not partner_uuid:
            return None

        res_partner = request.env["res.partner"].sudo()
        res_users = request.env["res.users"].sudo()

        partner = res_partner.search([["uuid", "=", partner_uuid]], limit=1)
        partner = partner.sudo()

        redirect_page_request = local_redirect(f"/my/{redirect_page}", kwargs)

        if not partner:
            # partner does not exist
            return redirect_page_request

        user = res_users.search([["partner_id", "=", partner.id]], limit=1)

        if user and not user.created_with_magic_link:
            # user already have an account not created with the magic link
            # this will ask him to log in then redirect him on the route asked
            return redirect_page_request

        if not user:
            # don't have a res_user must be created
            login = MyAccountController._create_magic_user_from_partner(partner)
        else:
            # already have a res_user created with a magic link
            login = user.login

        MyAccountController._reset_password_and_authenticate(login)

        return redirect_page_request

    @staticmethod
    def _reset_password_and_authenticate(login):
        # create a random password
        password = secrets.token_urlsafe(16)

        # reset password
        crypt_context = CryptContext(schemes=["pbkdf2_sha512", "plaintext"], deprecated=["plaintext"])
        password_encrypted = crypt_context.encrypt(password)
        request.env.cr.execute("UPDATE res_users SET password=%s WHERE login=%s;", [password_encrypted, login])
        request.env.cr.commit()

        # authenticate
        request.session.authenticate(request.session.db, login, password)
        return True

    @staticmethod
    def _create_magic_user_from_partner(partner):
        res_users = request.env["res.users"].sudo()

        values = {
            # ensure a login when the partner doesnt have an email
            "login": partner.email or "magic_login_" + secrets.token_urlsafe(16),
            "partner_id": partner.id,
            "created_with_magic_link": True,
        }

        # create a signup_token and create the account
        partner.signup_prepare()
        _, login, _ = res_users.signup(values=values, token=partner.signup_token)
        return login

    @route(["/my", "/my/home", "/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        # All this paths needs to be redirected
        partner = request.env.user.partner_id
        if not partner.primary_segment_id and not partner.write_and_pray:
            # Redirect to the segmentation survey
            survey = request.env.ref(
                "partner_compassion.partner_segmentation_survey").sudo()
            return request.redirect(urlparse(survey.public_url).path)
        if partner.sponsorship_ids:
            return request.redirect("/my/children")
        else:
            return request.redirect("/my/information")

    @route("/my/contact", type="http", auth="user", website=True)
    def contact_us(self, **kwargs):

        partner = request.env.user.partner_id

        kwargs["form_model_key"] = "cms.form.claim.contact.us"
        kwargs["partner_id"] = partner

        claim_form = self.get_form("crm.claim", **kwargs)

        claim_form.form_process()

        return request.render(
            "website_compassion.contact_us_page_template",
            {"partner": partner,
             "form": claim_form}
        )

    @route("/my/letter", type="http", auth="user", website=True)
    def my_letter(self, child_id=None, template_id=None, **kwargs):
        """
        The route to write new letters to a selected child
        :param child_id: the id of the selected child
        :param template_id: the id of the selected template
        :param kwargs: additional arguments (optional)
        :return: a redirection to a webpage
        """
        children = _get_user_children("write")
        if len(children) == 0:
            return request.render("website_compassion.sponsor_a_child", {})

        if not child_id:
            return request.redirect(
                f"/my/letter?child_id={children[0].id}&template_id={template_id or ''}"
                f"&{urlencode(kwargs)}")

        child = children.filtered(lambda c: c.id == int(child_id))
        if not child:  # The user does not sponsor this child_id
            return request.redirect(
                f"/my/letter?child_id={children[0].id}"
            )
        templates = request.env["correspondence.template"].search([
            ("active", "=", True),
            ("website_published", "=", True),
        ]).sorted(lambda t: "0" if "christmas" in t.name else t.name)
        if not template_id and len(templates) > 0:
            template_id = templates[0].id
        template = templates.filtered(lambda t: t.id == int(template_id))
        auto_texts = {}
        if "auto_christmas" in kwargs:
            for c in children:
                auto_texts[c.id] = CHRISTMAS_TEXTS.get(
                    c.field_office_id.primary_language_id.code_iso,
                    CHRISTMAS_TEXTS["eng"]
                ) % (c.preferred_name, request.env.user.partner_id.firstname)
        return request.render(
            "website_compassion.letter_page_template",
            {
                "child_id": child,
                "template_id": template,
                "children": children,
                "templates": templates,
                "partner": request.env.user.partner_id,
                "auto_texts": auto_texts
            }
        )

    @route("/my/children", type="http", auth="user", website=True)
    def my_child(self, state="active", child_id=None, **kwargs):
        """
        The route to see all the partner's children information
        :param state: the state of the children's sponsorships (active or
        terminated)
        :param child_id: the id of the child
        :param kwargs: optional additional arguments
        :return: a redirection to a webpage
        """
        actives = _get_user_children("active")
        terminated = _get_user_children("terminated") - actives

        display_state = True
        # User can choose among groups if none of the two is empty
        if len(actives) == 0 or len(terminated) == 0:
            display_state = False

        # We get the children group that we want to display
        if state == "active" and len(actives) > 0:
            children = actives
        else:
            children = terminated
            state = "terminated"

        # No sponsor children
        if len(children) == 0:
            return request.render("website_compassion.sponsor_a_child", {})

        # No child is selected, we pick the first one by default
        if not child_id:
            return request.redirect(f"/my/children?child_id={children[0].id}")

        # A child is selected
        child = children.filtered(lambda c: c.id == int(child_id))

        # The user does not sponsor this child_id
        if not child:
            return request.redirect(f"/my/children?state={state}&child_id={children[0].id}")

        # This child is sponsored by this user and is selected
        partner = request.env.user.partner_id
        correspondence_obj = request.env["correspondence"]
        correspondent = partner

        if partner.portal_sponsorships == "all_info":
            correspondent |= child.sponsorship_ids.filtered(
                lambda x: x.is_active).mapped("correspondent_id")
            correspondence_obj = correspondence_obj.sudo()

        letters = correspondence_obj.search([
            ("partner_id", "in", correspondent.ids),
            ("child_id", "=", int(child_id)),
            "|",
            "&", ("direction", "=", "Supporter To Beneficiary"),
            ("state", "!=", "Quality check unsuccessful"),
            "&", "&", ("state", "=", "Published to Global Partner"),
            ("letter_image", "!=", False),
            "|", ("communication_id", "=", False), ("sent_date", "!=", False)
        ])
        gift_categ = request.env.ref("sponsorship_compassion.product_category_gift")
        lines = request.env["account.invoice.line"].sudo().search([
            ("partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("contract_id.child_id", "=", child.id),
            ("product_id.categ_id", "=", gift_categ.id),
            ("price_total", "!=", 0),
        ])
        request.session['child_id'] = child.id

        gift_base_url = _("https://compassion.ch/de/geschenkformular")
        child_gift_params = partner.with_context({'mailchimp_child': child}).wordpress_form_data
        url_child_gift = f"{gift_base_url}?{child_gift_params}"

        context = {
            "child_id": child,
            "children": children,
            "letters": letters,
            "lines": lines,
            "state": state,
            "display_state": display_state,
            "url_child_gift": url_child_gift,
        }
        return request.render("website_compassion.my_children_page_template", context)

    @route("/my/donations/upgrade", type="http", auth="user", website=True)
    def my_donations_update(self, recurring_contract=None, new_amount=None, **kw):
        write_and_pray_max = 42
        sponsorship_max = 50
        # check if the arguments are valid
        # if not redirect to the donation page
        try:
            assert recurring_contract is not None
            recurring_contract = int(recurring_contract)
            partner = request.env.user.partner_id
            partner_contracts = partner.contracts_fully_managed + partner.contracts_paid
            contract = partner_contracts.filtered(
                lambda c: c.id == recurring_contract
                          and c.state not in ["cancelled", "terminated"]
            )
            assert len(contract) == 1
            # ensure that the write and pray can manage paid sponsorship
            assert contract.type not in ["SWP"] or partner.can_manage_paid_sponsorships

            max_amount = write_and_pray_max if contract.type in ["SWP"] else sponsorship_max

            # only write and pray can select the amount
            new_amount = int(new_amount) if new_amount and contract.type in ["SWP"] else max_amount

            # can only increase the amount and must be in the range
            assert max(1, contract.total_amount) < new_amount <= max_amount
        except (ValueError, AssertionError):
            return request.redirect("/my/donations")

        if "confirmed" not in kw:
            upgrade_url = f"/my/donations/upgrade?confirmed&recurring_contract={contract.id}"
            if new_amount:
                upgrade_url += f"&new_amount={new_amount}"
            context = {
                "new_amount": new_amount,
                "upgrade_url": upgrade_url,
            }
            return request.render("website_compassion.my_donations_update_confirmation", context)

        def create_line(fund_name, amount):
            product_template = request.env["product.template"].sudo()
            product_template = product_template.search([("default_code", "=", fund_name)], limit=1)
            return (0, 0, {
                "product_id": product_template.id,
                "quantity": 1,
                "amount": amount,
            })
        sponsorship_amount = min(write_and_pray_max, new_amount)
        contract_lines = [(5, 0, 0), create_line("sponsorship", sponsorship_amount)]
        remain = new_amount - sponsorship_amount
        if remain > 0:
            contract_lines.append(create_line("fund_gen", remain))
        contract.sudo().write({"contract_line_ids": contract_lines})

        return request.redirect("/my/donations")

    @route("/my/donations/submit_have_parent_consent", type="http", auth="user", website=True)
    def my_donations_submit_have_parent_consent(self, parent_consent=None, **kw):
        if parent_consent is None:
            return request.redirect("/my/donations")
        env = request.env
        partner = env.user.partner_id

        data = base64.b64encode(parent_consent.read())
        date = datetime.today().isoformat(sep="T", timespec="seconds")
        name = f"parent_consent_{date}_{parent_consent.filename}"

        env["ir.attachment"].create({
            "res_model": "res.partner",
            "res_id": partner.id,
            "name": name,
            "db_datas": data,
            "mimetype": parent_consent.content_type
        })
        partner.write({"parent_consent": "waiting"})
        return request.redirect("/my/donations")

    @route("/my/donations", type="http", auth="user", website=True)
    def my_donations(self, invoice_page='1', form_id=None, invoice_per_page=30, **kw):
        """
        The route to the donations and invoicing page
        :param invoice_page: index of the invoice pagination
        :param invoice_per_page: the number of invoices to display per page
        :param form_id: the id of the filled form or None
        :param kw: additional optional arguments
        :return: a redirection to a webpage
        """
        partner = request.env.user.partner_id

        invoice_page = int(invoice_page) if invoice_page.isnumeric() else 1

        invoice_search_criteria = [
            ("partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("type", "=", "out_invoice"),
            ("amount_total", "!=", 0),
        ]

        sudo_invoice_env = request.env["account.invoice"].sudo()

        all_invoice_count = sudo_invoice_env.search_count(invoice_search_criteria)

        invoice_per_page = int(invoice_per_page) if isinstance(invoice_per_page, str) else invoice_per_page
        invoice_page = invoice_page if invoice_page >= 1 and (
                invoice_page - 1) * invoice_per_page < all_invoice_count else 1

        count_invoice_pages = int(ceil(all_invoice_count / invoice_per_page))

        # invoice to show for the given pagination index
        invoices = sudo_invoice_env.search(invoice_search_criteria,
                                           offset=(invoice_page - 1) * invoice_per_page,
                                           limit=invoice_per_page)

        in_one_month = datetime.today() + timedelta(days=30)
        due_invoices = sudo_invoice_env.search([
            ("partner_id", "=", partner.id),
            ("state", "=", "open"),
            ("invoice_category", "=", "sponsorship"),
            ("type", "=", "out_invoice"),
            ("amount_total", "!=", 0),
            ("date_invoice", "<", fields.Date.to_string(in_one_month))
        ])

        last_completed_tax_receipt = partner.last_completed_tax_receipt

        groups = partner.sponsorship_ids.filtered(
            lambda s: s.state not in ["cancelled", "terminated"] and partner == s.mapped("partner_id")
        ).mapped("group_id")

        # List of recordset of sponsorships (one recordset for each group)
        sponsorships_by_group = [
            g.mapped("contract_ids").filtered(
                lambda c: c.state not in ["cancelled", "terminated"] and
                          c.partner_id == partner
            ) for g in groups
        ]
        # List of integers representing the total amount by group
        amount_by_group = [
            sum(list(filter(
                lambda a: a != 42.0,
                sponsor.filtered(lambda s: s.type == "S")
                    .mapped("contract_line_ids").mapped("amount")
            ))) for sponsor in sponsorships_by_group
        ]
        # List of recordset of paid sponsorships (one recordset for each group)
        paid_sponsor_count_by_group = [
            len(sponsorship.filtered(lambda s: s.type == "S"))
            for sponsorship in sponsorships_by_group
        ]
        paid_sponsor = (partner.contracts_fully_managed
                        + partner.contracts_paid) \
            .filtered(lambda a: a.state not in ["cancelled", "terminated"])
        # List of recordset of write and pray sponsorships (one recordset for each group)
        wp_sponsor_count_by_group = [
            len(sponsorship.filtered(lambda s: s.type in ["SC", "SWP"]))
            for sponsorship in sponsorships_by_group
        ]

        # List of strings (one bvr reference for each group)
        bvr_references = groups.mapped("bvr_reference")
        # Find the first non empty bvr reference in the groups
        bvr_reference = next((ref for ref in bvr_references if ref), None)
        # If no bvr reference is found, we compute a new one
        if not bvr_reference and groups:
            bvr_reference = groups[0].compute_partner_bvr_ref()
        elif not bvr_reference:
            bvr_reference = ""

        # Load forms
        form_success = False
        # Set the right form according to the number of groups
        if len(groups) > 1:
            kw["form_model_key"] = "cms.form.payment.options.multiple"
        else:
            kw["form_model_key"] = "cms.form.payment.options"
        # We pass some arguments to the form
        kw["total_amount"] = sum(amount_by_group)
        kw["bvr_reference"] = bvr_reference
        # This allows translations to work
        kw.pop("edit_translations", False)
        payment_options_form = self.get_form(
            "recurring.contract.group", groups[:1].id, **kw
        )
        if form_id is None or form_id == payment_options_form.form_id:
            payment_options_form.form_process()
            form_success = payment_options_form.form_success

        create_date = sudo_invoice_env.search([
            ("partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("type", "=", "out_invoice"),
            ("amount_total", "!=", 0),
        ], limit=1, order="create_date asc").create_date

        current_year = datetime.today().year
        first_year = create_date.year if create_date else current_year

        currency = (paid_sponsor.mapped("invoice_line_ids.currency_id.name") or [False])[0] or "CHF"
        upgrade_button_format = f"{_('Upgrade to %')} {currency}"

        upgrade_default_new_amount = {}
        upgrade_max_amount = {}
        for sponsor in paid_sponsor:
            value = sponsor.total_amount + 10
            sponsorships_max_amount = 42 if sponsor.type in ["SWP"] else 50
            # constrain between 1 and sponsorships_max_amount
            value = max(1, min(sponsorships_max_amount, value))
            upgrade_default_new_amount[sponsor.id] = value
            upgrade_max_amount[sponsor.id] = sponsorships_max_amount

        values = self._prepare_portal_layout_values()
        values.update({
            "partner": partner,
            "paid_sponsor": paid_sponsor,
            "payment_options_form": payment_options_form,
            "invoices": invoices,
            "invoice_page": invoice_page,
            "count_invoice_pages": count_invoice_pages,
            "due_invoices": due_invoices,
            "groups": groups,
            "amount_by_group": amount_by_group,
            "paid_sponsor_count_by_group": paid_sponsor_count_by_group,
            "wp_sponsor_count_by_group": wp_sponsor_count_by_group,
            "first_year": first_year,
            "current_year": current_year,
            "last_completed_tax_receipt": last_completed_tax_receipt,
            "upgrade_default_new_amount": upgrade_default_new_amount,
            "upgrade_max_amount": upgrade_max_amount,
            "upgrade_button_format": upgrade_button_format,
        })

        # This fixes an issue that forms fail after first submission
        if form_success:
            result = request.redirect("/my/donations")
        else:
            result = request.render(
                "website_compassion.my_donations_page_template", values
            )
        return result

    @route("/my/information", type="http", auth="user", website=True)
    def my_information(self, form_id=None, **kw):
        """
        The route to display the information about the partner
        :param form_id: the form that has been filled or None
        :param kw: the additional optional arguments
        :return: a redirection to a webpage
        """
        partner = request.env.user.partner_id

        def get_form(form_model_key):
            form = self.get_form("res.partner", partner.id, form_model_key=form_model_key, **kw)
            if form_id is None or form_id == form.form_id:
                form.form_process()
            return form

        coordinates_form = get_form("cms.form.partner.my.coordinates")
        # This fixes an issue that forms fail after first submission
        if coordinates_form.form_success:
            return request.redirect("/my/information")

        delivery_form = get_form("cms.form.partner.delivery")
        if delivery_form.form_success:
            return request.redirect("/my/information")

        values = self._prepare_portal_layout_values()
        values.update({
            "partner": partner,
            "coordinates_form": coordinates_form,
            "delivery_form": delivery_form,
        })

        return request.render("website_compassion.my_information_page_template", values)

    @route("/my/picture", type="http", auth="user", website=True, method="POST",
           sitemap=False)
    def save_ambassador_picture(self, **post):
        """
        The route to change the profile picture of a partner
        :param post: the argument received through the POST call
        :return: a redirection to a webpage
        """
        partner = request.env.user.partner_id
        picture_post = post.get("picture")
        if picture_post:
            image_value = compress_big_images(b64encode(picture_post.stream.read()))
            if not image_value:
                return "no image uploaded"
            partner.write({"image": image_value})
        return request.redirect("/my/information")

    @route("/my/download/<source>", type="http", auth="user", website=True)
    def download_file(self, source, **kw):
        """
        The route to download a file, that is either the tax receipt or an
        image
        :param source: Tells whether we want an image or a tax receipt
        :param kw: the additional optional arguments
        :return: a response to download the file
        """

        def _get_required_param(key, params):
            if key not in params:
                raise ValueError("Required parameter {}".format(key))
            return params[key]

        if source == "picture":
            child_id = int(kw.get("child_id", -1))
            obj_id = int(kw.get("obj_id", -1))
            return _download_image(child_id, obj_id)

        elif source == "tax_receipt":
            partner = request.env.user.partner_id
            year = _get_required_param("year", kw)

            wizard = request.env["print.tax_receipt"] \
                .with_context(active_ids=partner.ids).create({
                "pdf": True,
                "year": year,
                "pdf_name": _("tax_receipt") + f"_{year}.pdf",
            })
            wizard.get_report()
            headers = Headers()
            headers.add(
                "Content-Disposition", "attachment", filename=wizard.pdf_name
            )
            data = b64decode(wizard.pdf_download)
            return Response(data, content_type="application/pdf", headers=headers)

        elif source == "sponsorship_bvr":
            partner = request.env.user.partner_id
            # list active sponsorship where current user is partner (and not only correspondent)
            active_sponsorship = partner.sponsorship_ids.filtered(
                lambda s: s.state not in ["cancelled", "terminated"] and s.partner_id == partner)

            wizard = request.env["print.sponsorship.bvr"] \
                .with_context(active_ids=active_sponsorship.mapped("id")).sudo().create({
                "pdf": True,
                "paper_format": "report_compassion.bvr_sponsorship",
            })
            wizard.get_report()
            headers = Headers()
            headers.add(
                "Content-Disposition", "attachment", filename=wizard.pdf_name
            )
            data = b64decode(wizard.pdf_download)
            return Response(data, content_type="application/pdf", headers=headers)

        elif source == "gift_bvr":
            partner = request.env.user.partner_id
            child_id = int(_get_required_param("child_id", kw))

            sponsorship = partner.sponsorship_ids.filtered(
                lambda s: s.state not in ["cancelled", "terminated"] and s.child_id.id == child_id)

            wizard = request.env["print.sponsorship.gift.bvr"] \
                .with_context(active_ids=sponsorship.id, active_model="recurring.contract").sudo().create({
                "pdf": True,
                "paper_format": "report_compassion.bvr_gift_sponsorship",
                "draw_background": True
            })
            wizard.get_report()
            headers = Headers()
            headers.add(
                "Content-Disposition", "attachment", filename=wizard.pdf_name
            )
            data = b64decode(wizard.pdf_download)
            return Response(data, content_type="application/pdf", headers=headers)

        elif source == "labels":
            child_id = _get_required_param("child_id", kw)
            child = request.env["compassion.child"].browse(int(child_id))
            sponsorships = child.sponsorship_ids[0]
            label_print = request.env["label.print"].search(
                [("name", "=", "Sponsorship Label")], limit=1
            )
            label_brand = request.env["label.brand"].search(
                [("brand_name", "=", "Herma A4")], limit=1
            )
            label_format = request.env["label.config"].search(
                [("name", "=", "4455 SuperPrint WeiB")], limit=1
            )
            report_context = {
                "active_ids": sponsorships.ids,
                "active_model": "recurring.contract",
                "label_print": label_print.id,
                "must_skip_send_to_printer": True,
            }
            label_wizard = (
                request.env["label.print.wizard"]
                    .with_context(report_context)
                    .create(
                    {
                        "brand_id": label_brand.id,
                        "config_id": label_format.id,
                        "number_of_labels": 33,
                    }
                )
            )

            label_data = label_wizard.get_report_data()
            report_name = "label.report_label"
            report = (
                request.env["ir.actions.report"]
                    ._get_report_from_name(report_name)
                    .with_context(report_context)
            )
            pdf_data = report.with_context(
                must_skip_send_to_printer=True
            ).sudo().render_qweb_pdf(label_data['doc_ids'], data=label_data)[0]
            pdf_download = base64.encodebytes(pdf_data)
            headers = Headers()
            headers.add(
                "Content-Disposition", "attachment",
                filename=_("labels") + f"_{child.preferred_name}.pdf"
            )
            return Response(b64decode(pdf_download), content_type="application/pdf", headers=headers)
