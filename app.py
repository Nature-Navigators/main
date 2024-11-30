from flask import Flask, render_template, url_for, redirect, request, jsonify, redirect, send_from_directory, flash, session, g
from sqlalchemy import select, desc
from sqlalchemy.sql.expression import func
import uuid
import requests
import random
import folium
import os
import xyzservices.providers as xyz #Can use this to change map type
from urllib.parse import quote
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Email, InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt
from db_models import db, User, Post, Event, Favorite, PostImage, ProfileImage, PostLike, EventImage, Comment
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from helpers import *
from flask_mail import Mail, Message
from geopy.geocoders import Nominatim
from geopy.geocoders import OpenCage
import traceback
import requests
from flask_migrate import Migrate
from math import radians, sin, cos, sqrt, atan2 #for haversine formula
import babel
from functools import cmp_to_key
import asyncio
import aiohttp
import time
import logging
from PIL import Image
from io import BytesIO
from folium.plugins import Search
from folium.plugins import Geocoder
import base64
import os
from dotenv import load_dotenv

# load environment vars
load_dotenv()

# config app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 

app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.webp', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'
app.logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

EBIRD_API_RECENT_BIRDS_URL = 'https://api.ebird.org/v2/data/obs/geo/recent' 
EBIRD_API_KEY = os.getenv('EBIRD_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY') #for getting coordinates

@app.before_request
def before_request():
    g.geo_user = os.getenv('GEO_USER') #save geonames username for api calls


# Below array contains hardcoded birds from which a random bird is chosen for the "Wing it" page
random_birds = ['Black-winged Stilt', 'Laughing Kookaburra', 'Comb-crested Jacana', 
                'Black-necked Stilt', 'Red-crested Cardinal', 'Black Noddy', 'Red Avadavat',
                'Lesser Yellowlegs', 'Rosy-faced Lovebird', 'Eastern Rosella', 'Masked Lapwing',
                'California Quail', 'Monk Parakeet', 'Killdeer', 'Indigo Bunting', 'Hooded Warbler',
                'Bananaquit', 'Burrowing Owl', 'Carolina Wren', 'Painted Bunting', 'Talamanca Hummingbird',
                'Keel-billed Toucan', 'Long-tailed Broadbill', 'Large-billed Crow', 'Stork-billed Kingfisher',
                'Forest Wagtail']

# init database
db.init_app(app)

bcrypt = Bcrypt(app) # for password hashing
login_manager = LoginManager() # to manage pages accessible only to logged in users

login_manager.init_app(app)
login_manager.login_view = "signin"

geolocator = Nominatim(user_agent="event_locator")

migrate = Migrate(app, db)

# create database
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    return db.session.get(User, user_id)



@app.context_processor
def inject_user():
    return {'user': current_user}

# configure flask-mail for sending emails
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587 #  mail server port
app.config['MAIL_USE_TLS']= True # TLS encryption
# env variables
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PW')
mail = Mail(app) # Initialize mail object with Flask app

class SignUpForm(FlaskForm):
    # Form fields for sign-up
    # email, username, pw, confirm_pw mandatory fields
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})  
    username = StringField(validators=[InputRequired(), Length(min=1, max=200)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=1, max=200)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), Length(min=1, max=200), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField("Sign Up")
    
    # Validation for username
    # signing up requires unique username and email
    def validate_username(self, username):
        # check if another account already exists with same username
        # select user from db if their username matches the username entered in form
        exists_user = db.session.scalars(select(User.userID).where(User.username == username.data)).first()
        if exists_user != None:
            raise ValidationError("Username already exists. Select a new username.")
    # Validation for email
    def validate_email(self, email):
        # select user if their email matches the email entered
        # if user does exist raise validation error
        exists_email = db.session.scalars(select(User.userID).where(User.email == email.data)).first()
        if exists_email != None:
            raise ValidationError("Email already exists. Use another email address.")
   
class SignInForm(FlaskForm):
    # Form fields for sign-in
    # email, username, pw mandatory fields
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})  
    username = StringField(validators=[InputRequired(), Length(
        min=1, max=200)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=1, max=200)], render_kw={"placeholder": "Password"}) 
    remember = BooleanField('Remember Me')
    submit = SubmitField("Login")     
    
    # Validation for username
    def validate_username(self, username):
        # select user if their username matches the username entered
        exists_user = db.session.scalars(select(User.userID).where(User.username == username.data)).first()
        if exists_user == None:
            raise ValidationError("Username does not exist.")
    # Validation for email
    def validate_email(self, email):
        # select user if their email matches the email entered
        # fetch from db
        exists_email = db.session.scalars(select(User.userID).where(User.email == email.data)).first()
        if exists_email == None:
            raise ValidationError("Email does not exist.")

class RequestResetForm(FlaskForm):
    # Form fields for requesting password reset
    # email required to request for reset pw
    email = StringField('Email', 
                        validators=[InputRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    # Validation for email
    def validate_email(self, email):
        # select user if their email matches the email entered
        stmt = select(User).where(User.email == email.data)
        # fetch user from the database
        exists_email = db.session.execute(stmt).scalars().first()
        if exists_email is None:
            raise ValidationError("Email not associated with any account, try signing up.")
        
class ResetPasswordForm(FlaskForm):
    # Form fields for resetting password
    # pw required to reset pw
    password = PasswordField('Password', 
                             validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# This route serves the homepage
# It randomly selects a bird name from a list and renders the 'index.html' template
@app.route('/')
def index():
    bird_name = random.choice(random_birds)
    return render_template('index.html', bird_name=bird_name)

# This route serves the map page and passes API keys for Google Maps and eBird to the front end
@app.route('/map')
def map():
    return render_template(
        "map.html", 
        google_maps_api_key=GOOGLE_MAPS_API_KEY,
        ebird_api_key=EBIRD_API_KEY 
    )

# Function that receives POST request from front end with location data
# Retrieves nearby birds from eBird API and renders map
@app.route('/update_location', methods=['POST'])
async def update_location():

    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']
    bird_data = []
    
    birds_near_user = await getRecentBirds(latitude, longitude) # Fetch recent bird sightings near specifies location

    # Initialize folium map with user location, radius circle, full screen plugins
    m = folium.Map(location=[latitude, longitude], zoom_start=11)
    folium.Marker([latitude, longitude], tooltip='Your Location').add_to(m)

    folium.Circle(
    location=(latitude,longitude), 
    radius=30000, 
    fill_color='cornflowerblue', 
    stroke=True,
    fill=True,
    fill_opacity=0.25).add_to(m)

    folium.plugins.Fullscreen(
    position="topright",
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
    ).add_to(m)

    # Fetch images for each bird sighting from Wikipedia asynchronously
    tasks = []
    for bird in birds_near_user:
        bird_name = bird.get('comName')
        formatted_bird_name = formatBirdName(bird_name)
        tasks.append(getWikipediaImage(formatted_bird_name))
    image_urls = await asyncio.gather(*tasks) # wait for all Wikipedia image fetch tasks to complete

    # For each bird sighting add marker on map with a popup containing bird's information
    for i, bird in enumerate(birds_near_user):
        bird_name = bird.get('comName')
        bird_lat = bird.get('lat')
        bird_long = bird.get('lng')
        bird_url = f'/bird/{quote(bird_name)}'
        bird_code = bird.get('speciesCode')
        description = f"{bird_name} spotted near your location."
        
        bird_data.append({
            'title': bird_name,
            'speciesCode': bird_code,
            'imageUrl': image_urls[i],
            'description': description,
            'url': f'/bird/{quote(bird_name)}'
        })

        # content for the popup (link to more details and bird image)
        popup_content = f'''
        <a href="{bird_url}" target="_blank" style="display:block; width:100%; height:100%;">
            <b>{bird_name}</b> - Click for more details
        </a>
        <img src="{image_urls[i] if image_urls[i] else '/static/images/oop.png'}" 
            width="{150 if not image_urls[i] else 200}" />
        '''

        folium.Marker( # add marker to map
            location=[bird_lat, bird_long],
            tooltip=bird_name,
            icon=folium.Icon(color='orange'),
            popup=popup_content,
            lazy=True
        ).add_to(m)
    
    map_html = m._repr_html_() # get html of map

    return jsonify(mapHtml=map_html, birdData=bird_data)

# Helper function that takes in two coordinates and calculates distance between them in miles
def calculate_distance(lat1, lon1, lat2, lon2): 
    #earth radius
    R = 3958.8

    #converting locations to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    #haversine formula
    #credit to https://medium.com/@manishsingh7163/calculating-distance-between-successive-latitude-longitude-coordinates-using-pandas-287c15bc5029
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    #get distance in miles
    distance = R * c
    return distance

# This route allows the frontend to update map with bird sightings for the "All recent sightings" feature
@app.route('/update_map_with_bird_sightings', methods=['POST'])
def update_map_with_bird_sightings():
    data = request.get_json()
    
    bird_sightings = data['birdSightings']
    user_latitude = data['latitude']
    user_longitude = data['longitude']

    # folium marker with user location, full screen plugin, and radis circle
    m = folium.Map(location=[user_latitude, user_longitude], zoom_start=11)
    folium.Marker([user_latitude, user_longitude], popup="Your Location").add_to(m)

    folium.plugins.Fullscreen(
    position="topright",
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
    ).add_to(m)

    folium.Circle(
    location=(user_latitude,user_longitude), 
    radius=30000, 
    fill_color='cornflowerblue', 
    stroke=True,
    fill=True,
    fill_opacity=0.25).add_to(m)

    for sighting in bird_sightings:
        bird_lat = sighting['lat']
        bird_lng = sighting['lng']
        bird_name = sighting['comName']

        # uses haversine formula for distance display in icon popup
        distance = calculate_distance(user_latitude, user_longitude, bird_lat, bird_lng)
        popup_text = f"<b>{bird_name}</b><br>Spotted {distance:.2f} miles from you"
        
        folium.Marker(
            location=[bird_lat, bird_lng],
            icon=folium.Icon(color='purple'),
            popup=popup_text
        ).add_to(m)

    
    map_html = m._repr_html_()

    return jsonify({'mapHtml': map_html})

# Helper function that connects to eBird and gets recent bird sightings for a specified location
async def getRecentBirds(latitude, longitude):
    headers = {
        'X-eBirdApiToken': EBIRD_API_KEY
    }
    params = {
        'lat': latitude,
        'lng': longitude,
        'dist': 30  # Distance in km for observations
    }

    # Use aiohttp to asynchronously send a GET request to eBird API, used for speed optimization
    async with aiohttp.ClientSession() as session:
        async with session.get(EBIRD_API_RECENT_BIRDS_URL, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return []

# Helper function to format bird names to a specific format for compatibility with Wikipedia API   
def formatBirdName(bird_name):
    bird_name = bird_name.replace(' ', '_')

    parts = bird_name.split('_')

    formatted_name = parts[0]

    if len(parts) > 1:
        formatted_name += '_' + '_'.join(part.lower() for part in parts[1:])

    return formatted_name

async def getWikipediaImage(bird_name):

    formatted_bird_name = bird_name
    search_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={formatted_bird_name}&prop=pageimages&format=json&pithumbsize=500'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status == 200:
                data = await response.json()
                pages = data.get('query', {}).get('pages', {})
                for page_id, page in pages.items():
                    image_url = page.get('thumbnail', {}).get('source')
                    if image_url:
                        return image_url
            else:
                print(f"Failed to fetch data from Wikipedia. Status code: {response.status}")
    return None

async def getWikipediaPageContent(bird_name):
    formatted_bird_name = formatBirdName(bird_name)
    content_url = f'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=true&explaintext=true&titles={formatted_bird_name}&format=json'
    img_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={formatted_bird_name}&prop=pageimages&format=json&pithumbsize=600'
    images_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={formatted_bird_name}&prop=images&format=json'

    async with aiohttp.ClientSession() as session:
        tasks = [
            session.get(content_url),
            session.get(img_url),
            session.get(images_url)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        content_response = responses[0]
        content = None
        if content_response.status == 200:
            content_data = await content_response.json()
            pages = content_data.get('query', {}).get('pages', {})
            content = next(iter(pages.values())).get('extract', '')
        else:
            print(f"Failed to fetch content. Status code: {content_response.status}")

        img_response = responses[1]
        image_url = None
        if img_response.status == 200:
            img_data = await img_response.json()
            pages = img_data.get('query', {}).get('pages', {})
            first_page = next(iter(pages.values()), {})
            image_url = first_page.get('thumbnail', {}).get('source')
        else:
            print(f"Failed to fetch image. Status code: {img_response.status}")

        images_response = responses[2]
        image_urls = []
        if images_response.status == 200:
            img_data = await images_response.json()
            pages = img_data.get('query', {}).get('pages', {})
            first_page = next(iter(pages.values()), {})
            images = first_page.get('images', [])

            for img in images:
                img_title = img.get('title')
                if img_title:
                    if img_title.startswith('File:'):
                        img_filename = img_title[5:]

                        if img_filename.lower() == 'commons-logo.svg':
                            continue

                        bird_name_words = bird_name.lower().split()
                        if any(word in img_filename.lower() for word in bird_name_words):
                            file_url = f'https://en.wikipedia.org/wiki/Special:FilePath/{img_filename}'
                            image_urls.append(file_url)

        wiki = f'https://en.wikipedia.org/wiki/{formatted_bird_name}'

        return {
            'content': content,
            'imageUrl': image_url,
            'imageUrls': image_urls,
            'wikiUrl': wiki
        }

async def get_bird_info(bird_name):
    bird_data = await getWikipediaPageContent(bird_name)
    return {
        'imageUrl': bird_data['imageUrl'],
        'title': bird_name,
        'content': bird_data['content'],
        'imageUrls': bird_data['imageUrls'],
        'wikiUrl': bird_data['wikiUrl']
    }

@app.route('/bird/<bird_name>')
async def bird_page(bird_name):
    bird_data = await get_bird_info(bird_name)
    return render_template('bird.html', bird=bird_data)

@app.route('/signin', methods=['GET','POST'])

def signin():
     # If the user is already authenticated, redirect them to their profile page
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    # Create an instance of the sign-in form
    form = SignInForm()
    # Check if the form is submitted and validated
    if form.validate_on_submit():
            # Query the database to find the user by username and email
            found_id = db.session.scalars(select(User.userID).where(User.username == form.username.data, User.email == form.email.data)).first()
            # If the user is found
            if found_id != None:
                user = db.session.get(User, found_id)
                # Check if the provided password matches the stored password
                if not bcrypt.check_password_hash(user.password, form.password.data):
                    # If the password is incorrect, add an error message to the form
                    form.password.errors.append("Incorrect password.")
                else:
                    # If the password is correct, log in the user and redirect to their profile
                    login_user(user, remember=True)
                    profile_route = 'profile/' + user.username
                    return redirect(profile_route)
            else:
                # If the user is not found, raise validation error
                raise ValidationError("Invalid username or email. Try signing up or check the information entered")        
                # Render sign-in template with the form
    return render_template("signin.html", form=form)

@app.route('/logout')
def logout():
    # Log out the current user
    logout_user()
    # Redirect to the index page
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If the user is already authenticated, redirect them to their profile page
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    # Create an instance of the sign-up form
    form = SignUpForm()
    alert_message = ""
    # Check if the form is submitted and validated
    if form.validate_on_submit():
        # Hash the provided password
        hashed_passwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Create a new user instance
        new_user = User(userID=uuid.uuid4(),email=form.email.data, username=form.username.data, password=hashed_passwd)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            # Redirect to the sign-in page
            return redirect(url_for('signin'))
        except IntegrityError:
            # If there is an integrity error (e.g., username already exists), rollback the transaction
            db.session.rollback()  
            alert_message = "Username already exists. Select a new username."
            # Render the sign-up template with the form and alert message
    return render_template("signup.html", form=form, alert_message=alert_message)

# routes to a profile page as /profile/username
@app.route('/profile/<profile_id>', methods=['POST', 'GET'])
@login_required
def profile_id(profile_id):
  
    current_profile = None
    selected_id = None
    
    # attempt to get the user object from the database by searching for the username (which is unique)
    try:
        selected_id = db.session.scalars(select(User.userID).where(User.username == profile_id)).first()
        if selected_id != None:
            current_profile = db.session.get(User, selected_id)
    except Exception as error:
        print(error)
        return "There was an error loading the profile"

    # POST happens on "edit profile" submit
    if request.method == 'POST' and "edit_profile_name" in request.form:
        
        # grab data from the form
        new_name = request.form["edit_profile_name"]
        last_name = request.form["edit_profile_last_name"]
        pronouns = request.form["pronouns"]
        bio = request.form["bio"]
        image = request.files["image_file_bytes"]

        try:
            # if the user exists & is the one logged in
            if selected_id != None and selected_id == current_user.userID:

                # update anything that's changed                
                if current_profile.firstName != new_name:
                    current_profile.firstName = new_name

                if current_profile.lastName != last_name:
                    current_profile.lastName = last_name

                if current_profile.pronouns != pronouns:
                    current_profile.pronouns = pronouns

                if current_profile.bio != bio:
                    current_profile.bio = bio

                # if an image is being uploaded
                if image.filename != '':

                    filename = clean_image_filename(image)
                    
                    # filename checks out
                    if filename:                   
                        success = upload_image(filename, image, app.config)

                        if success:
                            imgPath = app.config["UPLOAD_PATH"] + "/" + filename

                            # delete original profile image
                            if current_profile.profileImage != None:
                                os.remove(os.path.join(app.config["UPLOAD_PATH"], current_profile.profileImage.name))
                                db.session.delete(current_profile.profileImage)

                            dbImg = ProfileImage(imageID=uuid.uuid4(), userID=selected_id, name=filename, imagePath=imgPath)
                            db.session.add(dbImg)
                        else:
                            flash("There was an issue uploading your profile image. Please check that your filetype is supported.", category="error")
                            return redirect(profile_id)

                db.session.commit()
                return redirect(profile_id)
            
            # user either doesn't exist or is not the one logged in
            else:
                return redirect(profile_id)
            
        #any additional errors
        except Exception as error:
            print(error)
            return "There was an issue editing your profile"

    # POST happens on Add Photo submit button
    elif request.method == 'POST' and "add_photo_caption" in request.form:

        # get data from the form
        bird_id = request.form.get('add_bird_id')
        location_id = request.form.get('add_location')
        new_caption = request.form.get('add_photo_caption')

        #add the new post to the database
        try:
            # try to get the current user from the DB based on username
            if selected_id != None and selected_id == current_user.userID:

                # setting up & adding the post
                new_postID = uuid.uuid4()
                new_post = Post(postID=new_postID, caption=new_caption, birdID=bird_id, locationID=location_id, datePosted=datetime.now(), userID=selected_id)
                db.session.add(new_post)

                #handle the image upload
                image = request.files["image_file_bytes"]
                filename = clean_image_filename(image)
                
                if filename and filename != '':
                    
                    success = upload_image(filename, image, app.config)

                    if success:
                        imgPath = app.config["UPLOAD_PATH"] + "/" + filename
                        dbImg = PostImage(imageID=uuid.uuid4(), postID=new_postID, name=filename, imagePath=imgPath)
                        db.session.add(dbImg)

                    else:
                        flash("There was an issue uploading your file. Please ensure it is the proper image type.", category="error")
                        return redirect(profile_id)
                
                db.session.commit()

                return redirect(profile_id)

            # the user didn't exist
            else:
                flash("Posting image failed", category="error")
                return redirect(profile_id)
        
        #any additional errors
        except Exception as error:
            print(error)
            return "There was an issue adding a photo"
    
    # POST happens on deleting a post 
    elif request.method == 'POST' and "postID" in request.form:

        try:
            # if the profile page we're on belongs to the logged in user
            if current_profile != None and current_profile.userID == current_user.userID:

                selected_post = db.session.get(Post, uuid.UUID(request.form["postID"]))

                # if the post ID passed to the function belongs to the logged in user
                    # meant to avoid spoofing to delete someone else's post
                if selected_post.user.userID == current_user.userID:

                    # remove images
                    images = selected_post.images
                    for image in images:
                        os.remove(os.path.join(app.config["UPLOAD_PATH"], image.name))

                    db.session.delete(selected_post)
                    db.session.commit()
                    return redirect(profile_id)

        except Exception as error:
            print(error)
            return "There was an error deleting your post"
        return redirect(profile_id)

    # POST happens on follow button
    elif request.method == 'POST' and "followBtn" in request.form:

        # not on your own profile
        if selected_id != None and selected_id != current_user.userID:
            try:
                #follow
                if current_user not in current_profile.followedBy:
                    current_profile.followedBy.append(current_user)
                #unfollow
                else:
                    current_profile.followedBy.remove(current_user)

                db.session.commit()

            except Exception as error:
                print(error)
                return "There was an error following"

        return redirect(profile_id)

    # page is loaded normally / no POST requests
    else:

        if selected_id != None:
            user = db.session.get(User, selected_id)

            
            try:
                createdEvents = db.session.scalars(select(Event).where(Event.userID == selected_id)).all()
                image_path = {image.eventID: image.imagePath for image in db.session.execute(select(EventImage)).scalars().all()}   

                #serialize and include images
                createdEvents = [
                    {
                        **event.to_dict(),
                        "imagePath": image_path.get(event.eventID),
                    }
                    for event in createdEvents
                ] 
                
                #get fav eventIDs
                savedEventIDs = db.session.scalars(
                    select(Favorite.eventID).where(Favorite.userID == current_user.userID)
                ).all()

                # Fetch fav events corresponding to fav eventIDs
                savedEvents = db.session.scalars(
                    select(Event).where(Event.eventID.in_(savedEventIDs))
                ).all()

                savedEvents = [
                    {
                        **event.to_dict(),
                        "imagePath": image_path.get(event.eventID),
                    }
                    for event in savedEvents
                ]

                posts = user.to_dict()['posts']

            except Exception as error:
                print(traceback.format_exc())
                return "Recursion error encountered"

            logged_in = current_user.username == profile_id  #if the logged_in user is viewing their own profile
            is_following = current_user.userID != selected_id and current_user in current_profile.followedBy
            context = {
                "createdEvents": createdEvents,
                "savedEvents": savedEvents,
                "id" : profile_id,
                "user": user,
                "loggedIn": logged_in,
                "userPosts": posts,
                "isFollowing": is_following
            }
            return render_template("profile.html", **context)
        
        # nonexistent user
        else:
            return "User does not exist"

@app.route('/profile')
@login_required
def profile():

    #redirect to the signin page if not logged in
    if not current_user.is_authenticated:
        print(f"Not logged in")
        return redirect("signin")
    
    #if logged in
    profile_path = "profile/" + current_user.username
    return redirect(profile_path)


# converts datetime to easily human-readable string
@app.template_filter('datetimeformat')
def datetimeformat(value):
    parsed_date = datetime.strptime(value, '%Y-%m-%d %H:%M')
    return parsed_date.strftime("%B %d, %Y at %I:%M %p")


def get_coordinates(city_state):
    geolocator = OpenCage(OPENCAGE_API_KEY)
    location = geolocator.geocode(city_state)
    if location:
        return location.latitude, location.longitude
    else:
        print("Location not found.")
        return None


@app.route('/create_event', methods=['POST', 'GET'])
def create_event():

    if not current_user.is_authenticated: #identify loggedin/loggedout users 
        print(f"Not logged in")
        return jsonify({'error': 'Event not created, user not logged in'}), 401
    
    data = request.json

    event_image = data.get('image')
    imageName = data.get('imageName')

    title = data.get('title')
    description = data.get('description')
    creator =  current_user.userID 
    
    location = data.get('location')
    latitude, longitude = get_coordinates(location)

    event_date_str = data.get('eventDate')  
    event_time_str = data.get('time') 

    # Combine date and time
    combined_datetime_str = f"{event_date_str} {event_time_str}"
    dateAndTime = datetime.strptime(combined_datetime_str, '%Y-%m-%d %H:%M')

    temp_event_id = uuid.uuid4()  # random event ID
    
    new_event = Event(
            eventID = temp_event_id,
            title=title,
            description=description,
            eventDate=dateAndTime,
            userID=creator,
            location=location,
            latitude=latitude,
            longitude=longitude,
        )
    db.session.add(new_event)
    
    if event_image:
        #decode Base64 
        image_data = event_image.split(",")[1]  # remove "data:image/png;base64,"
        image_binary = base64.b64decode(image_data)

        # create file path
        file_path = app.config["UPLOAD_PATH"] + "/" + imageName
        
        # Write image data to file and save
        with open(file_path, "wb") as f:
            f.write(image_binary)

        # Save image details in db
        new_image = EventImage(imageID=uuid.uuid4(), eventID=temp_event_id, name=imageName, imagePath=file_path)
        db.session.add(new_image)

    db.session.commit()
        
    return jsonify({'success': True, 'message': 'Event created successfully!'})

# get event details to display in editModal when user wants to edit an event
@app.route('/get_event_details/<eventID>', methods=['GET'])
def get_event_details(eventID):
    event_id = uuid.UUID(eventID)
    event = db.session.scalars(select(Event).filter_by(eventID=event_id)).first()

    event_images = {image.eventID: {'imagePath': image.imagePath, 'imageName': image.name} 
                    for image in db.session.execute(select(EventImage)).scalars().all()}

    if event:
        return jsonify({
            'imagePath': event_images.get(event_id, {}).get('imagePath'),
            'imageName': event_images.get(event_id, {}).get('imageName'),
            'eventID': event.eventID,
            'title': event.title,
            'eventDate': event.eventDate.isoformat(),
            'location': event.location,
            'description': event.description
        })
    return jsonify({'error': 'Event not found'}), 404


@app.route('/edit_event', methods=['POST'])
def edit_event():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    event_id = uuid.UUID(data.get('eventID'))

    event = db.session.scalars(select(Event).filter_by(eventID=event_id)).first()
    

    if event:
        event.title = data.get('title')
        event.eventDate = datetime.strptime(
            f"{data.get('eventDate')} {data.get('time')}", '%Y-%m-%d %H:%M'
        )                                                                           #parse string to get date/time
        event.location = data.get('location')
        event.latitude, event.longitude = get_coordinates(data.get('location')) 
        event.description = data.get('description')
        db.session.commit()

        #get image 
        event_image = data.get('image')
        imageName = data.get('imageName')

        if event_image: 
            if event_image.startswith("data"): #if starts with http do nothing, image already exists in db
                #if the event has a user uploaded image associated with it

                existing_image = db.session.scalars(select(EventImage).filter_by(eventID=event_id)).first()

                #delete old img from database
                if (existing_image):
                    db.session.delete(existing_image)
                    db.session.commit()
                
                #decode Base64 
                image_data = event_image.split(",")[1]  # remove "data:image/png;base64,"
                image_binary = base64.b64decode(image_data)

                # create file path. imageName contains name of the image file uploaded
                file_path = app.config["UPLOAD_PATH"] + "/" + imageName
                
                # Write image data to file and save
                with open(file_path, "wb") as f:
                    f.write(image_binary)

                # Save image details in db
                new_image = EventImage(imageID=uuid.uuid4(), eventID=event_id, name=imageName, imagePath=file_path)
                db.session.add(new_image)
                db.session.commit()

        return jsonify({'success': True, 'message': 'Event updated successfully!'})
    
    return jsonify({'error': 'Event not found'}), 404


@app.route('/delete_event', methods=['POST'])
def delete_event():
    if not current_user.is_authenticated: 
        print("Not logged in")
        return jsonify({'error': 'Event not deleted, user not logged in'}), 401

    data = request.json
    event_id = uuid.UUID(data.get('eventID'))

    #find event where eventId matches the one sent and userID matches that of logged in user
    event = db.session.scalars(select(Event).filter_by(eventID=event_id, userID=current_user.userID)).first()

    #remove entry in favorites table if deleted event is favorited
    favorites = db.session.scalars(select(Favorite).filter_by(eventID=event_id)).all()
    for favorite in favorites:
        db.session.delete(favorite)

    if not event:
        return jsonify({'error': 'Event not found or you do not have permission to delete this event'}), 404

    db.session.delete(event)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Event deleted successfully!'})

   
@app.route('/favorite_event', methods=['POST'])
def favorite_event():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    eventID = uuid.UUID(data.get('eventID'))
    userID = current_user.userID  # Get the logged-in user's ID

    new_favorite = Favorite(userID=userID, eventID=eventID)

    # Add the favorite to the database
    try:
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Event favorited successfully!'})
    except IntegrityError:
        db.session.rollback()  #rollback if an error occurs
        return jsonify({'success': False, 'message': 'Event already favorited'})


@app.route('/unfavorite_event', methods=['POST'])
def unfavorite_event():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    user_id = current_user.userID
    event_id = uuid.UUID(data.get('eventID'))

    # Find the favorite entry to delete
    favorite = Favorite.query.filter_by(userID=user_id, eventID=event_id).first()
    favorite = db.session.scalars(select(Favorite).filter_by(userID=user_id, eventID=event_id)).first()
    
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Event removed from favorites successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Event not found in favorites'})


@app.route('/social_location', methods=['POST'])
def social_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    #max_distance_m = 1000

    #check which events are previously favorited by user
    if current_user.is_authenticated:
        favorited_event_ids = set(
            db.session.execute(
                select(Favorite.eventID).filter_by(userID=current_user.userID)
            ).scalars()
        )
    else:
        favorited_event_ids = set()

    #add a favorited flag if event exists in user fav list
    tempEvents = db.session.execute(select(Event)).scalars().all()
    image_path = {image.eventID: image.imagePath for image in db.session.execute(select(EventImage)).scalars().all()}   

    serialized_events = [
        {**event.to_dict(), "favorited": event.eventID in favorited_event_ids, "imagePath": image_path.get(event.eventID)}
        for event in tempEvents
    ]

    #sort events by distance
    events_with_distance = [
        (calculate_distance(latitude, longitude, event.get('latitude'), event.get('longitude')), event)
        for event in serialized_events
    ]

    #x[0] holds the distance calculated, and the events are sorted according to it
    events_with_distance.sort(key=lambda x: x[0])

    #extracts only event data to send to client
    sorted_events = [event for _, event in events_with_distance]

    return jsonify(sorted_events)


@app.route('/social', methods=["GET","POST"])
def social():   

    # global variable that controls whether the "following only" toggle is on or ont
    if session.get('shouldOnlyFollowers') == None:
        session['shouldOnlyFollowers'] = True


    # get the posts
    posts = []
    shouldFillPosts = True # False only on searching

    # user hit enter on the search bar
    if request.method == 'POST' and "usernameSearch" in request.form:
        text = request.form["usernameSearch"]

        text = text.lower()
        if text != '':
            result = None
            if session['shouldOnlyFollowers'] and current_user.is_authenticated:
                following = current_user.following
                
                # find the username in the following list
                for follower in following:
                    if follower.username == text:
                        result = follower
                        break
            
            # look for the user outside of following
            else:
                result = db.session.scalars(select(User).where(func.lower(User.username) == text)).first()
            
            if result != None:
                posts = [post.to_dict() for post in result.posts]

            shouldFillPosts = False
            
    # checkbox update    
    elif request.method == 'POST':
        # form has nothing in it if it's an "off" checkbox
        if len(request.form) == 0:
            session['shouldOnlyFollowers'] = False
        elif "toggle" in request.form:
            session['shouldOnlyFollowers'] = True
        

    if current_user.is_authenticated:
        favorited_event_ids = set(
            db.session.execute(
                select(Favorite.eventID).filter_by(userID=current_user.userID)
            ).scalars()
        )
    else:
        favorited_event_ids = set()

    dbPostGrabLimit = 50

    try:
        # user logged in and toggle should only be followers
        if current_user.is_authenticated and session['shouldOnlyFollowers'] and shouldFillPosts:

            if current_user.following:

                following = current_user.following
                followingPosts = []
                
                # append all posts
                for follower in following:
                    
                    followerObj = db.session.get(User, follower.userID)

                    for post in followerObj.posts:
                        post_dict = post.to_dict()
                        post_dict['user'] = followerObj.to_dict()
                        followingPosts.append(post_dict)

                # get followers' most liked posts
                posts = sorted(followingPosts, key = cmp_to_key(lambda post1, post2 : post2["likes_count"]-post1["likes_count"]))

        # user not logged in, get top (most liked) posts
        elif shouldFillPosts:
            # add the posts to the list
            dbPosts = db.session.scalars(select(Post).order_by(desc(Post.likes_count)).limit(dbPostGrabLimit)).all()
            for dbPost in dbPosts:
                post_dict = dbPost.to_dict()
                post_dict['user'] = dbPost.user.to_dict()
                posts.append(post_dict)

        
    except Exception as error:
        print(traceback.format_exc())

    #add a favorited flag if event exists in user fav list
    tempEvents = db.session.execute(select(Event)).scalars().all()

    # get image paths for each event
    image_path = {image.eventID: image.imagePath for image in db.session.execute(select(EventImage)).scalars().all()}   

    serialized_events = [
        {**event.to_dict(), "favorited": event.eventID in favorited_event_ids, "imagePath": image_path.get(event.eventID)}
        for event in tempEvents
    ]

    logged_in = current_user.is_authenticated

    context = {
        "events": serialized_events,
        "posts": posts,
        "followersOnly": session['shouldOnlyFollowers'],
        "loggedIn": logged_in
    }

    return render_template('social.html', **context)

# make a string into a datetime
@app.template_filter()
def format_datetime(value, format='medium'):

    convertedStr = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') 
    if format == 'full':
        format="EEEE, d. MMMM y 'at' h:mm a"
    elif format == 'medium':
        format="dd/MM/y 'at' h:mm a"
    return babel.dates.format_datetime(convertedStr, format)

@app.route('/bird')
def bird():
    return render_template("bird.html")

def get_map_html():
    # This function can be used to create and return the initial map HTML
    m = folium.Map(location=[37.7749, -122.4194], zoom_start=13)  # Example starting location
    return m._repr_html_()

# used for getting uploaded images from the database via url_for
@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_PATH"], filename, as_attachment=True)

def send_email(user):
    try:
        # Generate a password reset token for the user
        token = user.get_reset_token()
        # Create a new email message
        msg = Message('Password Reset Request', sender='noreply@featherly.com', recipients=[user.email])
        msg.body = f'''To reset your password, click the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, ignore this email
'''
        # Send the email
        mail.send(msg)
    except Exception as e:
        raise ValidationError("Error sending email")

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    # If the user is already authenticated, redirect them to their profile page
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    # Create an instance of the password reset request form
    form = RequestResetForm()
    # Check if the form is submitted and validated
    if form.validate_on_submit():
        # Query the database to find the user by email
        user = db.session.scalars(select(User).where(User.email == form.email.data)).first()
        # If the user is found, send a password reset email
        if user:
            send_email(user)
        else:
            raise ValidationError('User not found')
        # Redirect to the sign-in page
        return redirect(url_for('signin'))
    # Render the password reset request template with the form
    return render_template('reset_req.html', title='Reset password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    # If the user is already authenticated, redirect them to their profile page
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    # Verify the password reset token
    user = User.verify_reset_token(token)
    # If the token is invalid or expired, raise a validation error and redirect to the reset request page
    if user is None:
        raise ValidationError('That is an invalid or expired token')
        return redirect(url_for('reset_request'))
    
    # Create an instance of the password reset form
    form = ResetPasswordForm()
    # Check if the form is submitted and validated
    if form.validate_on_submit():
        # Hash the new password
        hashed_passwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Update the user's password in the database
        user.password = hashed_passwd        
        db.session.commit()
        # Redirect to the sign-in page
        return redirect(url_for('signin'))
    # Render the password reset template with the form
    return render_template('reset.html', title='Reset Password', form=form)

@app.route('/api/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    if not current_user.is_authenticated: #identify loggedin/loggedout users 
        return jsonify({'error': 'user not logged in'}), 401
    
    try:
        # Convert the post ID to a UUID
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        # If the post ID is not a valid UUID, return an error response
        return jsonify({'error': 'Invalid post ID format'}), 400
    
    # Query the database to find the post by ID
    post = db.session.scalars(select(Post).filter_by(postID=post_uuid)).first()
    # If the post is not found, return an error response
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Query the database to find if the current user has already liked the post
    like = db.session.scalars(select(PostLike).filter_by(userID=current_user.userID, postID=post_uuid)).first()

    if like:
        # If the user has already liked the post, remove the like and decrement the like count
        db.session.delete(like)
        post.likes_count -= 1
        liked = False
    else:
        # If the user has not liked the post, add a new like and increment the like count
        new_like = PostLike(userID=current_user.userID, postID=post_uuid)
        db.session.add(new_like)
        post.likes_count += 1
        liked = True
    # Commit the changes to the database
    db.session.commit()
    # Return the updated like count and like status
    return jsonify({'likes': post.likes_count, 'liked': liked}), 200

@app.route('/api/posts/<post_id>/like/status', methods=['GET'])
@login_required
def get_like_status(post_id):
    try:
        # Convert the post ID to a UUID
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        # If the post ID is not a valid UUID, return an error response
        return jsonify({'error': 'Invalid post ID format'}), 400
    # Query the database to find the post by ID
    post = db.session.scalars(select(Post).filter_by(postID=post_uuid)).first()
    # If the post is not found, return an error response
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check if the current user has liked the post
    liked = db.session.scalars(select(PostLike).filter_by(userID=current_user.userID, postID=post_uuid)).first() is not None
    # Return the like status and like count
    return jsonify({'liked': liked, 'likes': post.likes_count}), 200


@app.route('/create-comment/<post_id>', methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('comment')

    if not text:
        return jsonify({'error': 'Comment cannot be empty'}), 400

    post_uuid = uuid.UUID(post_id)
    post = db.session.scalars(select(Post).filter_by(postID=post_uuid)).first()
    if post:
        comment = Comment(commentID=uuid.uuid4(), text=text, postID=post_uuid, username=current_user.username, dateCommented=datetime.now())
        db.session.add(comment)
        db.session.commit()
        response = {'success': True, 'message': 'Comment added successfully!', 'username': current_user.username}
        return jsonify(response), 200
    else:
        return jsonify({'error': 'Post not found'}), 404
    

@app.route('/search_by_bird', methods=['POST'])
def search_by_bird():
    bird_id = request.form.get('birdIDSearch')
    if not bird_id:
        flash('birdID parameter is required', 'error')
        return redirect(url_for('social'))

    # to allow for partial matching 
    bird_id = f"%{bird_id}%"

    if session.get('shouldOnlyFollowers', True) and current_user.is_authenticated:
        following_ids = [user.userID for user in current_user.following]
        posts = db.session.scalars(select(Post).filter(Post.birdID.ilike(bird_id), Post.userID.in_(following_ids))).all()
    else:
        posts = db.session.scalars(select(Post).filter(Post.birdID.ilike(bird_id))).all()

    serialized_posts = [post.to_dict() for post in posts]

    context = {
        "posts": serialized_posts,
        "followersOnly": session.get('shouldOnlyFollowers', True),
        "loggedIn": current_user.is_authenticated
    }

    return render_template('social.html', **context)


if __name__ == "__main__":
    app.run()