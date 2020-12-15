##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime
from base64 import b64decode
from os import path, remove
from zipfile import ZipFile
from urllib.request import urlretrieve, urlopen

from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

from odoo.http import request, route
from odoo.addons.web.controllers.main import content_disposition
from odoo.addons.cms_form_compassion.controllers.payment_controller import (
    PaymentFormController,
)


def _map_contracts(partner, mapping_val=None, sorting_val=None,
                   filter_fun=lambda _: True):
    return (
        partner.contracts_fully_managed.filtered(filter_fun) +
        partner.contracts_correspondant.filtered(filter_fun) +
        partner.contracts_paid.filtered(filter_fun)
    ).mapped(mapping_val).sorted(sorting_val)


def _get_children(partner, only_active=False):
    """
    Find all the children for which the connected user has a contract. There is
    the possibility to fetch all chidren from contracts or only those for which
    a sponsorship is active.
    :return: a recordset of child.compassion which the connected user sponsors
    """
    def filter_sponsorships(sponsorship):
        return not only_active or sponsorship.state == "active"

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
            urlretrieve(img.image_url, filename)
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
        partner = request.env.user.partner_id
        children = _get_children(partner)
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
    @route(["/my", "/my/home", "/my/account"], type='http', auth="user", website=True)
    def account(self, redirect=None, **post):
        return request.redirect("/my/information")

    @route("/my/letter", type="http", auth="user", website=True)
    def my_letter(self, child_id=None, template_id=None, **kwargs):
        partner = request.env.user.partner_id
        children = _get_children(partner, only_active=True)
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
                 "templates": templates},
            )
        else:
            return request.redirect(f"/my/letter?child_id={children[0].id}")

    @route("/my/children", type="http", auth="user", website=True)
    def my_child(self, child_id=None, **kwargs):
        partner = request.env.user.partner_id
        children = _get_children(partner)

        if len(children) == 0:
            return request.render("website_compassion.sponsor_a_child", {})

        if child_id:
            child = children.filtered(lambda c: c.id == int(child_id))
            if not child:  # The user does not sponsor this child_id
                return request.redirect(
                    f"/my/children?child_id={children[0].id}"
                )
            letters = request.env["correspondence"].search([
                ("partner_id", "=", partner.id),
                ("child_id", "=", int(child_id)),
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
            return request.render(
                "website_compassion.my_children_page_template",
                {"child_id": child,
                 "children": children,
                 "letters": letters,
                 "lines": lines}
            )
        else:
            return request.redirect(f"/my/children?child_id={children[0].id}")

    @route("/my/donations", type="http", auth="user", website=True)
    def my_donations(self, form_id=None, **kw):
        partner = request.env.user.partner_id

        invoices = request.env["account.invoice"].sudo().search([
            ("partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("invoice_type", "in", ["sponsorship", "fund", "other"]),
            ("type", "=", "out_invoice"),
            ("amount_total", "!=", 0),
        ])

        # Group related parametersl10n_ch.payment_slip
        groups = _map_contracts(
            partner, "group_id", filter_fun=lambda s: s.state not in
            ["cancelled", "terminated"] and partner == s.mapped("partner_id")
        )
        if not groups:
            request.redirect("/my/home")

        sponsorships_by_group = [
            g.mapped("contract_ids").filtered(
                lambda c: c.state not in ["cancelled", "terminated"] and
                c.partner_id == partner
            ) for g in groups
        ]
        amount_by_group = [
            sum(list(filter(
                lambda a: a != 42.0,
                sponsor.filtered(lambda s: s.type == "S")
                .mapped("contract_line_ids").mapped("amount")
            ))) for sponsor in sponsorships_by_group
        ]
        paid_sponsor_count_by_group = [
            len(sponsorship.filtered(lambda s: s.type == "S"))
            for sponsorship in sponsorships_by_group
        ]
        wp_sponsor_count_by_group = [
            len(sponsorship.filtered(lambda s: s.type == "SC"))
            for sponsorship in sponsorships_by_group
        ]
        bvr_references = groups.mapped("bvr_reference")
        bvr_reference = next((ref for ref in bvr_references if ref), None)
        if not bvr_reference:
            bvr_reference = groups[0].compute_partner_bvr_ref()

        # Load forms
        form_success = False
        if len(groups) > 1:
            kw["form_model_key"] = "cms.form.payment.options.multiple"
        else:
            kw["form_model_key"] = "cms.form.payment.options"
        kw["total_amount"] = sum(amount_by_group)
        kw["bvr_reference"] = bvr_reference
        payment_options_form = self.get_form(
            "recurring.contract.group", groups[0].id, **kw
        )
        if form_id is None or form_id == payment_options_form.form_id:
            payment_options_form.form_process()
            form_success = payment_options_form.form_success

        first_year = request.env["account.invoice"].sudo().search([
            ("partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("type", "=", "out_invoice"),
            ("amount_total", "!=", 0),
        ], limit=1, order="create_date asc").create_date.year
        current_year = datetime.today().year

        values = self._prepare_portal_layout_values()
        values.update({
            "partner": partner,
            "payment_options_form": payment_options_form,
            "invoices": invoices,
            "groups": groups,
            "sponsorships_by_group": sponsorships_by_group,
            "amount_by_group": amount_by_group,
            "paid_sponsor_count_by_group": paid_sponsor_count_by_group,
            "wp_sponsor_count_by_group": wp_sponsor_count_by_group,
            "first_year": first_year,
            "current_year": current_year,
        })

        # This fixes an issue that forms fail after first submission
        if form_success:
            result = request.redirect("/my/donations")
        else:
            result = request.render(
                "website_compassion.my_donations_page_template", values
            )
        return self._form_redirect(result, full_page=True)

    @route("/my/download/<source>", type="http", auth="user", website=True)
    def download_file(self, source, **kw):
        def _get_required_param(key, params):
            if key not in params:
                raise ValueError("Required parameter {}".format(key))
            return params[key]

        if source == "picture":
            child_id = _get_required_param("child_id", kw)
            obj_id = _get_required_param("obj_id", kw)

            if child_id and obj_id:
                return _download_image("single", child_id, obj_id)
            elif child_id:
                return _download_image("multiple", child_id)
            else:
                return _download_image("all")
        elif source == "tax_receipt":
            partner = request.env.user.partner_id
            year = _get_required_param("year", kw)

            wizard = request.env["print.tax_receipt"]\
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
