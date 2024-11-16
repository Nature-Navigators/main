from flask import Flask, render_template, url_for, redirect, request, jsonify, redirect, send_from_directory, flash, session
from sqlalchemy import select, desc
from sqlalchemy.sql.expression import func
import uuid
import requests
import folium
import os
import xyzservices.providers as xyz #Can use this to change map type
from temp_data import *
from urllib.parse import quote
# from markupsafe import Markup
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Email, InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt
from db_models import db, User, Post, Event, Favorite, PostImage, ProfileImage, PostLike
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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '4a0a3f65e0186d76a7cef61dd1a4ee7b'

app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.webp', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'
app.logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

EBIRD_API_RECENT_BIRDS_URL = 'https://api.ebird.org/v2/data/obs/geo/recent' 
EBIRD_API_KEY = os.environ['EBIRD_API_KEY']
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']



db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_view = "signin"

geolocator = Nominatim(user_agent="event_locator")

migrate = Migrate(app, db)

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

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS']= True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PW')
mail = Mail(app)
class SignUpForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})  
    username = StringField(validators=[InputRequired(), Length(min=1, max=200)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=1, max=200)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), Length(min=1, max=200), EqualTo('password')], render_kw={"placeholder": "Confirm_Password"})
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        exists_user = db.session.scalars(select(User.userID).where(User.username == username.data)).first()
        if exists_user != None:
            raise ValidationError("Username already exists. Select a new username.")

    def validate_email(self, email):
        exists_email = db.session.scalars(select(User.userID).where(User.email == email.data)).first()
        if exists_email != None:
            raise ValidationError("Email already exists. Use another email address.")
        
class SignInForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})  
    username = StringField(validators=[InputRequired(), Length(
        min=1, max=200)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=1, max=200)], render_kw={"placeholder": "Password"}) 
    remember = BooleanField('Remember Me')
    submit = SubmitField("Login")     

    def validate_username(self, username):
        exists_user = db.session.scalars(select(User.userID).where(User.username == username.data)).first()
        if exists_user == None:
            raise ValidationError("Username does not exist.")
    
    def validate_email(self, email):
        exists_email = db.session.scalars(select(User.userID).where(User.email == email.data)).first()
        if exists_email == None:
            raise ValidationError("Email does not exist.")

class RequestResetForm(FlaskForm):
    email = StringField('Email', 
                        validators=[InputRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        stmt = select(User).where(User.email == email.data)
        exists_email = db.session.execute(stmt).scalars().first()
        if exists_email is None:
            raise ValidationError("Email not associated with any account, try signing up.")
        
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', 
                             validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/map')
def map():
    return render_template(
        "map.html", 
        google_maps_api_key=GOOGLE_MAPS_API_KEY,
        ebird_api_key=EBIRD_API_KEY 
    )


@app.route('/update_location', methods=['POST'])
async def update_location():

    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']
    bird_data = []
    
    birds_near_user = await getRecentBirds(latitude, longitude)

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

    tasks = []
    for bird in birds_near_user:
        bird_name = bird.get('comName')
        formatted_bird_name = formatBirdName(bird_name)
        tasks.append(getWikipediaImage(formatted_bird_name))
    image_urls = await asyncio.gather(*tasks)

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

        popup_content = f'''
        <a href="{bird_url}" target="_blank" style="display:block; width:100%; height:100%;">
            <b>{bird_name}</b> - Click for more details
        </a>
        <img src="{image_urls[i]}" width="200"/>
        '''

        folium.Marker(
            location=[bird_lat, bird_long],
            tooltip=bird_name,
            icon=folium.Icon(color='orange'),
            popup=popup_content,
            lazy=True
        ).add_to(m)
    
    map_html = m._repr_html_()

    return jsonify(mapHtml=map_html, birdData=bird_data)

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
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    #get distance in miles
    distance = R * c
    return distance

@app.route('/update_map_with_bird_sightings', methods=['POST'])
def update_map_with_bird_sightings():
    data = request.get_json()
    
    bird_sightings = data['birdSightings']
    user_latitude = data['latitude']
    user_longitude = data['longitude']

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

        distance = calculate_distance(user_latitude, user_longitude, bird_lat, bird_lng)
        popup_text = f"<b>{bird_name}</b><br>Spotted {distance:.2f} miles from you"
        
        folium.Marker(
            location=[bird_lat, bird_lng],
            icon=folium.Icon(color='purple'),
            popup=popup_text
        ).add_to(m)

    
    map_html = m._repr_html_()

    return jsonify({'mapHtml': map_html})

async def getRecentBirds(latitude, longitude):
    headers = {
        'X-eBirdApiToken': EBIRD_API_KEY
    }
    params = {
        'lat': latitude,
        'lng': longitude,
        'dist': 30  # Distance in km for observations
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(EBIRD_API_RECENT_BIRDS_URL, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return []
    
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

def getWikipediaPageContent(bird_name):
    formatted_bird_name = formatBirdName(bird_name)
    content_url = f'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=true&explaintext=true&titles={formatted_bird_name}&format=json'
    img_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={formatted_bird_name}&prop=pageimages&format=json&pithumbsize=500'
    
    content_response = requests.get(content_url)
    content = None
    if content_response.status_code == 200:
        content_data = content_response.json()
        pages = content_data.get('query', {}).get('pages', {})
        content = next(iter(pages.values())).get('extract', '')
    else:
        print(f"Failed to fetch content. Status code: {content_response.status}")

    img_response = requests.get(img_url)
    image_url = None
    if img_response.status_code == 200:
        img_data = img_response.json()
        pages = img_data.get('query', {}).get('pages', {})
        first_page = next(iter(pages.values()), {})
        image_url = first_page.get('thumbnail', {}).get('source')

    else:
        print(f"Failed to fetch image. Status code: {img_response.status}")

    wiki = f'https://en.wikipedia.org/wiki/{formatted_bird_name}'

    return {
        'content': content,
        'imageUrl': image_url,
        'wikiUrl': wiki
    }

def get_bird_info(bird_name):
    bird_data = getWikipediaPageContent(bird_name)
    return {
        'imageUrl': bird_data['imageUrl'],
        'title': bird_name,
        'content': bird_data['content'],
        'wikiUrl': bird_data['wikiUrl']
    }

@app.route('/bird/<bird_name>')
def bird_page(bird_name):
    bird_info = get_bird_info(bird_name)
    return render_template('bird.html', bird=bird_info)

@app.route('/signin', methods=['GET','POST'])

def signin():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = SignInForm()
    if form.validate_on_submit():
            found_id = db.session.scalars(select(User.userID).where(User.username == form.username.data, User.email == form.email.data)).first()
            if found_id != None:
                user = db.session.get(User, found_id)
                if not bcrypt.check_password_hash(user.password, form.password.data):
                    #raise ValidationError("Incorrect password.")
                    form.password.errors.append("Incorrect password.")
                else:
                    login_user(user, remember=True)
                    profile_route = 'profile/' + user.username
                    return redirect(profile_route)
            else:
                raise ValidationError("Invalid username or email. Try signing up or check the information entered")        
    return render_template("signin.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = SignUpForm()
    alert_message = ""

    if form.validate_on_submit():
        hashed_passwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(userID=uuid.uuid4(),email=form.email.data, username=form.username.data, password=hashed_passwd)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('signin'))
        except IntegrityError:
            db.session.rollback()  
            alert_message = "Username already exists. Select a new username."

    return render_template("signup.html", form=form, alert_message=alert_message)


# TODO: adjust when we have users & logged-in users in the DB
@app.route('/profile/<profile_id>', methods=['POST', 'GET'])
@login_required
def profile_id(profile_id):
  
    current_profile = None
    selected_id = None
    
    try:
        selected_id = db.session.scalars(select(User.userID).where(User.username == profile_id)).first()
        if selected_id != None:
            current_profile = db.session.get(User, selected_id)
    except Exception as error:
        print(error)
        return "There was an error loading the profile"

    # POST happens on "edit profile" submit
    if request.method == 'POST' and "edit_profile_name" in request.form:
        
        new_name = request.form["edit_profile_name"]
        image = request.files["image_file_bytes"]

        try:
            # try to get the current profile from the DB based on username
            if selected_id != None and selected_id == current_user.userID:

                if current_profile.firstName != new_name:
                    current_profile.firstName = new_name

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
                #print(db.session.scalars(select(Image.name)).all())
                return redirect(profile_id)
            else:
                return redirect(profile_id)
        #any additional errors
        except Exception as error:
            print(error)
            return "There was an issue editing your profile"

    # POST happens on Add Photo submit button
    elif request.method == 'POST' and "add_photo_caption" in request.form:
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
                #TODO: post failed is a pop up
                return "User does not exist or user is not the one logged in; Posting image failed"
        
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

    # page is loaded normally
    else:

        if selected_id != None:
            user = db.session.get(User, selected_id)

            
            try:
                createdEvents = db.session.scalars(select(Event).where(Event.userID == selected_id)).all()
                #print(createdEvents)

                #get fav eventIDs
                savedEventIDs = db.session.scalars(
                    select(Favorite.eventID).where(Favorite.userID == current_user.userID)
                ).all()

                # Fetch fav events corresponding to fav eventIDs
                savedEvents = db.session.scalars(
                    select(Event).where(Event.eventID.in_(savedEventIDs))
                ).all()

                #print(savedEvents)

                #posts = []
                posts = user.to_dict()['posts']
                #print(user.to_dict())
            except Exception as error:
                print(traceback.format_exc())
                return "Recursion error encountered"

            logged_in = current_user.username == profile_id  #if the logged_in user is viewing their own profile
            is_following = current_user.userID != selected_id and current_user in current_profile.followedBy
            context = {
                "socialPosts": socialPosts,
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


@app.template_filter('datetimeformat')
def datetimeformat(value):
    #print(value)
    parsed_date = datetime.strptime(value, '%Y-%m-%d %H:%M')
    return parsed_date.strftime("%B %d, %Y at %I:%M %p")


def get_coordinates(city_state):
    geolocator = OpenCage(api_key="029ce9756caf4c8ab64c155f894d651e")
    location = geolocator.geocode(city_state)
    if location:
        return location.latitude, location.longitude
    else:
        print("Location not found.")
        return None


@app.route('/create_event', methods=['POST', 'GET'])
def create_event():

    #print(f"user id: ")
    #print(current_user.userID)

    if not current_user.is_authenticated: #identify loggedin/loggedout users 
        print(f"Not logged in")
        return jsonify({'error': 'Event not created, user not logged in'}), 401
    
    #print(f"logged in!")
    print(f"user id: ")
    print(current_user.userID)

    data = request.json

    title = data.get('title')
    description = data.get('description')
    creator =  current_user.userID 
    
    location = data.get('location')
    latitude, longitude = get_coordinates(location)

    event_date_str = data.get('eventDate')  # Assume this is in 'YYYY-MM-DD' format
    event_time_str = data.get('time')  # Assume this is in 'HH:MM' format

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
    db.session.commit()
        
    return jsonify({'success': True, 'message': 'Event created successfully!'})

#get event details to display in editModal
@app.route('/get_event_details/<eventID>', methods=['GET'])
def get_event_details(eventID):
    event_id = uuid.UUID(eventID)
    event = db.session.scalars(select(Event).filter_by(eventID=event_id)).first()

    if event:
        return jsonify({
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
        return jsonify({'success': True, 'message': 'Event updated successfully!'})
    
    return jsonify({'error': 'Event not found'}), 404


@app.route('/delete_event', methods=['POST'])
def delete_event():
    if not current_user.is_authenticated: 
        print("Not logged in")
        return jsonify({'error': 'Event not deleted, user not logged in'}), 401

    data = request.json
    event_id = uuid.UUID(data.get('eventID'))

    event = db.session.scalars(select(Event).filter_by(eventID=event_id, userID=current_user.userID)).first()

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



def haversine(lat1, lon1, lat2, lon2):
    R = 3959.0
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    #Haversine
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


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
    serialized_events = [
        {**event.to_dict(), "favorited": event.eventID in favorited_event_ids }
        for event in tempEvents
    ]

    #sort events by distance
    events_with_distance = [
        (haversine(latitude, longitude, event.get('latitude'), event.get('longitude')), event)
        for event in serialized_events
    ]

    events_with_distance.sort(key=lambda x: x[0])
    sorted_events = [event for _, event in events_with_distance]

    #print(f"Filtered Events: {sorted_events}")
    return jsonify(sorted_events)


@app.route('/social', methods=["GET","POST"])
def social():   

    if session.get('shouldOnlyFollowers') == None:
        session['shouldOnlyFollowers'] = True


    # get the posts
    posts = []
    shouldFillPosts = True # False only on searching

    # hit enter on the search bar
    if request.method == 'POST' and "usernameSearch" in request.form:
        text = request.form["usernameSearch"]

        #TODO: LIKE (edit distance) instead of exact matches
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

    #TODO: change to use DB 
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
    serialized_events = [
        {**event.to_dict(), "favorited": event.eventID in favorited_event_ids }
        for event in tempEvents
    ]

    context = {
        "events": serialized_events,
        "posts": posts,
        "followersOnly": session['shouldOnlyFollowers']
    }

    return render_template('social.html', **context)

@app.template_filter()
def format_datetime(value, format='medium'):
    #print(value)
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

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_PATH"], filename, as_attachment=True)

def send_email(user):
    try:
        token = user.get_reset_token()
        print(f"Generated token: {token}")  # Debugging statement
        msg = Message('Password Reset Request', sender='noreply@featherly.com', recipients=[user.email])
        msg.body = f'''To reset your password, click the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, ignore this email
'''
        mail.send(msg)
        print("Email sent successfully")  # Debugging statement
    except Exception as e:
        print(f"Error sending email: {e}")  # Debugging statement

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.session.scalars(select(User).where(User.email == form.email.data)).first()
        if user:
            send_email(user)
            print("send_email function called")  # Debugging statement
        else:
            print("User not found")  # Debugging statement
        return redirect(url_for('signin'))
    return render_template('reset_req.html', title='Reset password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    user = User.verify_reset_token(token)
    if user is None:
        raise ValidationError('That is an invalid or expired token')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_passwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_passwd        
        db.session.commit()
        return redirect(url_for('signin'))
    return render_template('reset.html', title='Reset Password', form=form)

@app.route('/api/posts/<post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    try:
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        return jsonify({'error': 'Invalid post ID format'}), 400

    post = db.session.scalars(select(Post).filter_by(postID=post_uuid)).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    like = db.session.scalars(select(PostLike).filter_by(userID=current_user.userID, postID=post_uuid)).first()

    if like:
        db.session.delete(like)
        post.likes_count -= 1
        liked = False
    else:
        new_like = PostLike(userID=current_user.userID, postID=post_uuid)
        db.session.add(new_like)
        post.likes_count += 1
        liked = True

    db.session.commit()
    return jsonify({'likes': post.likes_count, 'liked': liked}), 200

@app.route('/api/posts/<post_id>/like/status', methods=['GET'])
@login_required
def get_like_status(post_id):
    try:
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        return jsonify({'error': 'Invalid post ID format'}), 400

    post = db.session.scalars(select(Post).filter_by(postID=post_uuid)).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    liked = db.session.scalars(select(PostLike).filter_by(userID=current_user.userID, postID=post_uuid)).first() is not None
    return jsonify({'liked': liked, 'likes': post.likes_count}), 200

if __name__ == "__main__":
    app.run(debug=True)