import base64
from io import BytesIO
from PIL import Image

def compress_big_images(b64_data, max_width=900, max_height=400, max_bytes_size=2e5):
    """
    Method that tries to compress an image receveived as parameter if this
    image is too big (greater than 200KB). If the image is small enough or
    if the compression does not improve the results, we simply return the
    old version of the image.

    :param max_bytes_size: The maximum allowed image size in byte
    :param max_height: height resize threshold
    :param max_width: width resize threshold
    :param b64_data: the data of the image to compress, expressed as a
    base64 string.
    :return: either the original image, if it is small enough (<200KB)
    or if the compression does not reduce size, or a new image that has
    been compressed, again as a base64 string.
    """

    def resize(image):
        width, height = image.size
        _width, _height = min(width, max_width), min(height, max_height)
        factor = min(_width / width, _height / height)
        return image.resize((int(width * factor), int(height * factor)))

    def compress(image):
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format='JPEG', optimize=True)
        return base64.b64encode(buffer.getvalue())

    old_image = b64_data
    # If length in byte is greater than 200KB
    bytes_len = 3 * (len(b64_data) / 4)
    if bytes_len > max_bytes_size:
        bytes_data = BytesIO(base64.b64decode(b64_data))
        img = Image.open(bytes_data)
        new_image = compress(resize(img))
        new_bytes_len = 3 * (len(new_image) / 4)
        # We don't change the image if there is no improvement
        return new_image if bytes_len > new_bytes_len else old_image
    return old_image