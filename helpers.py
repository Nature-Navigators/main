# helpers.py: contains helper functions that don't rely on app
import uuid
import imghdr
from werkzeug.utils import secure_filename
from sqlalchemy import select
from db_models import db, Image
import os

# determines what type of image format is given based on byte stream
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return "." + (format if format != "jpeg" else "jpg")

# makes sure there's no duplicates
def clean_image_filename(image):
    #handle the image upload
    filename = secure_filename(image.filename)

    if filename == '':
        return ''

    # check to see if the filename exists in the database
    matching_name = db.session.scalars(select(Image).where(Image.name == filename))
    if matching_name != None:
        #add a unique ID to the start in case it already exists
        unique_str = str(uuid.uuid4())[:8]
        image.filename = f"{unique_str}_{image.filename}"
    
    filename = secure_filename(image.filename)
    return filename

# uploading an image file into the database
def upload_image(filename, image, config):
    file_ext = os.path.splitext(filename)[1]

    #check that the extension is valid
    if file_ext not in config["UPLOAD_EXTENSIONS"] or file_ext != validate_image(image.stream):
        return False
    
    # save it & create the DB object
    image.save(os.path.join(config["UPLOAD_PATH"], filename))
    return True