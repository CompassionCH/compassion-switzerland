##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from os import path, remove
from zipfile import ZipFile
from urllib.request import urlretrieve, urlopen

from odoo.http import request, route
from odoo.addons.web.controllers.main import content_disposition
from odoo.addons.cms_form_compassion.controllers.payment_controller import (
    PaymentFormController
)


def _get_user_children():
    """
    Find all the children for which the connected user has a contract.
    :return: a recordset of child.compassion which the connected user sponsors
    """
    partner = request.env.user.partner_id
    return (
        partner.contracts_fully_managed +
        partner.contracts_correspondant +
        partner.contracts_paid
    ).mapped("child_id").sorted("preferred_name")


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
                   f"{image.date}_{child.code}.{ext}"
        folder = f"{child.preferred_name}_{child.code}"
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
    with ZipFile(archive_name, 'w') as archive:
        for (img, full_path) in images:
            filename = path.basename(full_path)

            # Create file, write to archive and delete it from os
            urlretrieve(img.image_url, filename)
            archive.write(filename, full_path)
            remove(filename)

    # Get binary content of the archive, then delete the latter
    archive = open(archive_name, "rb")
    zip_data = archive.read()
    archive.close()
    remove(archive_name)

    return request.make_response(
        zip_data,
        [("Content-Type", "application/zip"),
         ("Content-Disposition", content_disposition(archive_name))]
    )


def _download_image(type, obj_id, child_id):
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
            f"{child.preferred_name}_{child.code}.zip"
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
    @route("/my", type="http", auth="user", website=True)
    def home(self, **kw):
        return request.redirect("/my/home")

    @route("/my/home", type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        return request.render("website_compassion.my_account_layout", {})

    @route("/my/download/<source>", type="http", auth="user", website=True)
    def download_file(self, source, obj_id=None, child_id=None, **kw):
        if source == "picture":
            if child_id and obj_id:
                return _download_image("single", obj_id, child_id)
            elif child_id:
                return _download_image("multiple", obj_id, child_id)
            else:
                return _download_image("all", obj_id, child_id)

    @route("/my/children", type="http", auth="user", website=True)
    def my_children(self, **kwargs):
        children = _get_user_children()
        if len(children) == 0:
            return request.render(
                "website_compassion.my_children_empty_page_content", {}
            )
        else:
            return request.redirect(f"/my/child/{children[0].id}")

    @route("/my/child/<int:child_id>", type="http", auth="user", website=True)
    def my_child(self, child_id, **kwargs):
        partner = request.env.user.partner_id
        children = _get_user_children()
        child = children.filtered(lambda child: child.id == child_id)
        lines = request.env["account.invoice.line"].search([
            ("partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("contract_id.child_id", "=", child.id),
            ("product_id.categ_id.id", "=", 5),
            ("price_total", "!=", 0),
        ])
        if not child:
            return request.redirect(f"/my/children")
        else:
            child.get_infos()
            return request.render(
                "website_compassion.my_children_page_template",
                {"child_id": child,
                 "line_ids": lines},
            )
