# helpers.py: contains helper functions that don't rely on app to keep things clean

import imghdr

# determines what type of image format is given based on byte stream
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return "." + (format if format != "jpeg" else "jpg")