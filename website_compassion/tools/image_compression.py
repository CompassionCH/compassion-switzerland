import base64
from io import BytesIO
from PIL import Image
from odoo.tools.image import image_resize_image

def compress_big_images(b64_data, max_width=900, max_height=400):
    """
    Resize an image to fit into a specific box size

    :param b64_data: the data of the image to compress, expressed as a
    base64 string.
    :param max_width: width of the box
    :param max_height: height of the box

    :return: the compressed image in b64
    """
    if isinstance(b64_data, str):
        b64_data = base64.b64encode(base64.b64decode(b64_data))
    return image_resize_image(b64_data, size=(max_width, max_height), avoid_if_small=True)
