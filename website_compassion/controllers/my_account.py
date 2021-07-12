##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import datetime, timedelta
from base64 import b64decode, b64encode
from os import path, remove
from urllib.parse import urlparse
from zipfile import ZipFile
from urllib.request import urlretrieve, urlopen
from math import ceil
from dateutil.relativedelta import relativedelta

from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

from odoo import fields
from odoo.http import request, route
from odoo.addons.web.controllers.main import content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.cms_form_compassion.controllers.payment_controller import (
    PaymentFormController,
)

from ..tools.image_compression import compress_big_images


def _map_contracts(partner, mapping_val=None, sorting_val=None,
                   filter_fun=lambda _: True):
    """
    Map the contracts accordingly to the given values
    :param partner: the partner to map contracts from
    :param mapping_val: optional value to use for the mapping
    :param sorting_val: optional sorting value to use
    :param filter_fun: optional filter function
    :return:
    """
    return (
            partner.contracts_fully_managed.filtered(filter_fun) +
            partner.contracts_correspondant.filtered(filter_fun) +
            partner.contracts_paid.filtered(filter_fun)
    ).mapped(mapping_val).sorted(sorting_val)


def _get_user_children(state=None):
    """
    Find all the children for which the connected user has a contract for.
    There is the possibility to fetch either only active chidren or only those
    that are terminated / cancelled. By default, all sponsorships are returned

    :return: a recordset of child.compassion which the connected user sponsors
    """
    partner = request.env.user.partner_id
    only_correspondent = partner.app_displayed_sponsorships == "correspondent"

    limit_date = datetime.now() - relativedelta(months=2)

    exit_comm_config = list(
        map(lambda x: partner.env.ref("partner_communication_switzerland." + x).id, [
            "lifecycle_child_planned_exit", "lifecycle_child_unplanned_exit"]))

    end_reason_child_depart = partner.env.ref(
        "sponsorship_compassion.end_reason_depart")

    def filter_sponsorships(sponsorship):

        exit_comm_to_send = not partner.env["partner.communication.job"].search_count([
            ("partner_id", "=", partner.id),
            ("config_id", "in", exit_comm_config),
            ("state", "=", "done"),
            ("object_ids", "like", sponsorship.id)
        ])

        can_show = True
        is_recent_terminated = (
                sponsorship.state == "terminated"
                and sponsorship.end_date and sponsorship.end_date >= limit_date
                and sponsorship.end_reason_id == end_reason_child_depart)
        is_communication_not_sent = (sponsorship.state == "terminated"
                                     and exit_comm_to_send)
        if only_correspondent:
            can_show = sponsorship.correspondent_id == partner
        if state == "active":
            can_show &= sponsorship.state not in ["draft", "cancelled", "terminated"] \
                        or is_communication_not_sent or is_recent_terminated

        elif state == "terminated":
            can_show &= sponsorship.state in ["cancellled", "terminated"] and not \
                (is_recent_terminated and is_communication_not_sent)

        return can_show

    return _map_contracts(
        partner, mapping_val="child_id", sorting_val="preferred_name",
        filter_fun=filter_sponsorships
    )


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
            img_url = f'https://erp.compassion.ch/web/image/compassion.child.pictures/{img.id}/fullshot/'
            urlretrieve(img_url, filename)
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


def _download_image(type, child_id=None, obj_id=None):
    """
    Download one or multiple images (in a .zip archive if more than one) and
    return a response for the user to download it.
    :param type: the type of download, either 'single', 'multiple' or 'all'
    :param obj_id: the id of the image to download or None
    :param child_id: the id of the child to download from or None
    :return: A response for the user to download a single image or an archive
    containing multiples
    """
    if type == "all":  # We want to download all the images of all children
        children = _get_user_children()
        images = []
        for child in children:
            images += _fetch_images_from_child(child)
        return _create_archive(images, f"my_children_pictures.zip")

    child = request.env["compassion.child"].browse(int(child_id))

    if type == "multiple":  # We want to download all images from one child
        return _create_archive(
            _fetch_images_from_child(child),
            f"{child.preferred_name}_{child.local_id}.zip"
        )

    if type == "single":  # We want to download a single image from a child
        image = request.env["compassion.child.pictures"].browse(int(obj_id))

        # We get the extension and the binary content from URL
        ext = image.image_url.split(".")[-1]
        data = urlopen(image.image_url).read()
        filename = f"{child.preferred_name}_{image.date}.{ext}"

        return request.make_response(
            data,
            [("Content-Type", f"image/{ext}"),
             ("Content-Disposition", content_disposition(filename))]
        )


class MyAccountController(PaymentFormController):
    @route(["/my", "/my/home", "/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        # All this paths needs to be redirected
        partner = request.env.user.partner_id
        if not partner.primary_segment_id:
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
        children = _get_user_children("active")
        if len(children) == 0:
            return request.render("website_compassion.sponsor_a_child", {})

        if child_id:
            child = children.filtered(lambda c: c.id == int(child_id))
            if not child:  # The user does not sponsor this child_id
                return request.redirect(
                    f"/my/letter?child_id={children[0].id}"
                )
            templates = request.env["correspondence.template"].search([
                ("active", "=", True),
                ("website_published", "=", True),
            ]).sorted("name")
            if not template_id and len(templates) > 0:
                template_id = templates[0].id
            template = templates.filtered(lambda t: t.id == int(template_id))
            return request.render(
                "website_compassion.letter_page_template",
                {"child_id": child,
                 "template_id": template,
                 "children": children,
                 "templates": templates,
                 "partner": request.env.user.partner_id}
            )
        else:
            return request.redirect(f"/my/letter?child_id={children[0].id}")

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
        terminated = _get_user_children("terminated")
        actives = _get_user_children("active") - terminated

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

        # A child is selected
        if child_id:
            child = children.filtered(lambda c: c.id == int(child_id))
            if not child:  # The user does not sponsor this child_id
                return request.redirect(
                    f"/my/children?state={state}&child_id={children[0].id}"
                )
            partner = request.env.user.partner_id

            correspondence_obj = request.env["correspondence"]
            correspondent = partner

            if partner.app_displayed_sponsorships == "all_info":
                correspondent |= child.sponsorship_ids.filtered(lambda x: x.is_active).mapped("correspondent_id")
                correspondence_obj = correspondence_obj.sudo()

            letters = correspondence_obj.search([
                ("partner_id", "in", correspondent.ids),
                ("child_id", "=", int(child_id)),
                "|",
                "&", ("direction", "=", "Supporter To Beneficiary"),
                ("state", "!=", "Quality check unsuccessful"),
                "|", ("letter_delivered", "=", True), ("sent_date", "!=", False)
            ])
            gift_categ = request.env.ref(
                "sponsorship_compassion.product_category_gift"
            )
            lines = request.env["account.invoice.line"].sudo().search([
                ("partner_id", "=", partner.id),
                ("state", "=", "paid"),
                ("contract_id.child_id", "=", child.id),
                ("product_id.categ_id", "=", gift_categ.id),
                ("price_total", "!=", 0),
            ])
            request.session['child_id'] = child.id
            return request.render(
                "website_compassion.my_children_page_template",
                {"child_id": child,
                 "children": children,
                 "letters": letters,
                 "lines": lines,
                 "state": state,
                 "display_state": display_state}
            )
        else:
            # No child is selected, we pick the first one by default
            return request.redirect(f"/my/children?child_id={children[0].id}")

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
            ("invoice_category", "in", ["sponsorship", "fund", "other"]),
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

        groups = _map_contracts(
            partner, "group_id", filter_fun=lambda s: s.state not in
                                                      ["cancelled", "terminated"] and partner == s.mapped("partner_id")
        )
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
        # List of recordset of write and pray sponsorships (one recordset for each group)
        wp_sponsor_count_by_group = [
            len(sponsorship.filtered(lambda s: s.type == "SC"))
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

        values = self._prepare_portal_layout_values()
        values.update({
            "partner": partner,
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
            "last_completed_tax_receipt": last_completed_tax_receipt
        })

        # This fixes an issue that forms fail after first submission
        if form_success:
            result = request.redirect("/my/donations")
        else:
            result = request.render(
                "website_compassion.my_donations_page_template", values
            )
        return self._form_redirect(result, full_page=True)

    @route("/my/information", type="http", auth="user", website=True)
    def my_information(self, form_id=None, **kw):
        """
        The route to display the information about the partner
        :param form_id: the form that has been filled or None
        :param kw: the additional optional arguments
        :return: a redirection to a webpage
        """
        partner = request.env.user.partner_id

        # Load forms
        form_success = False
        kw["form_model_key"] = "cms.form.partner.my.coordinates"
        coordinates_form = self.get_form("res.partner", partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()
            form_success = coordinates_form.form_success

        kw["form_model_key"] = "cms.form.partner.delivery"
        delivery_form = self.get_form("res.partner", partner.id, **kw)
        if form_id is None or form_id == delivery_form.form_id:
            delivery_form.form_process()
            form_success = delivery_form.form_success

        values = self._prepare_portal_layout_values()
        values.update({
            "partner": partner,
            "coordinates_form": coordinates_form,
            "delivery_form": delivery_form,
        })

        # This fixes an issue that forms fail after first submission
        if form_success:
            result = request.redirect("/my/information")
        else:
            result = request.render(
                "website_compassion.my_information_page_template", values
            )
        return self._form_redirect(result, full_page=True)

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
            child_id = kw.get("child_id", False)
            obj_id = kw.get("obj_id", False)

            if child_id and obj_id:
                return _download_image("single", child_id, obj_id)
            elif child_id:
                return _download_image("multiple", child_id)
            else:
                return _download_image("all")
        elif source == "tax_receipt":
            partner = request.env.user.partner_id
            year = _get_required_param("year", kw)

            wizard = request.env["print.tax_receipt"] \
                .with_context(active_ids=partner.ids).create({
                "pdf": True,
                "year": year,
                "pdf_name": f"tax_receipt_{year}.pdf",
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
            actives = _get_user_children("active")
            child = actives.filtered(lambda c: c.id == int(child_id))
            sponsorships = child.sponsorship_ids[0]
            attachments = dict()
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
                "Content-Disposition", "attachment", filename=f"labels_{child.preferred_name}.pdf"
            )
            return Response(b64decode(pdf_download), content_type="application/pdf", headers=headers)
