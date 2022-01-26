import base64
from io import BytesIO
from PIL import Image


def compress_big_images(b64_data, max_width=900, max_height=400):
    """
    Resize an image to fit into a specific box size

    :param b64_data: the data of the image to compress, expressed as a
    base64 string.
    :param max_width: width of the box
    :param max_height: height of the box

    :return: the compressed image in b64
    """
    img = Image.open(BytesIO(base64.b64decode(b64_data)))
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    buffer = BytesIO()
    img.convert("RGB").save(buffer, format='JPEG', optimize=True)
    return base64.b64encode(buffer.getvalue())
