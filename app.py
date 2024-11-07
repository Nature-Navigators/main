from flask import Flask, render_template, url_for, redirect, request, jsonify, redirect, send_from_directory
from sqlalchemy import select
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
from db_models import db, User, Post, Event, Favorite, Image, PostImage
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from helpers import validate_image
from flask_mail import Mail, Message
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '4a0a3f65e0186d76a7cef61dd1a4ee7b'

app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.webp', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'

EBIRD_API_RECENT_BIRDS_URL = 'https://api.ebird.org/v2/data/obs/geo/recent' 
EBIRD_API_KEY = os.environ['EBIRD_API_KEY']
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']


db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_view = "signin"


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
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
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), Length(min=4, max=20), EqualTo('password')], render_kw={"placeholder": "Confirm_Password"})
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
        min=4, max=20)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"}) 
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
    return render_template("map.html", google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']
    
    page = data.get('page', 1)
    page_size = 3
    
    birds_near_user = getRecentBirds(latitude, longitude)


    m = folium.Map(location=[latitude, longitude], zoom_start=13)
    folium.Marker([latitude, longitude], tooltip='Your Location').add_to(m)

    for bird in birds_near_user:
        bird_name = bird.get('comName')
        bird_lat = bird.get('lat')
        bird_long = bird.get('lng')
        # formatted_bird_name = formatBirdName(bird_name)
        folium.Marker(
            location=[bird_lat, bird_long],
            tooltip=bird_name,
            icon=folium.Icon(color='red'),
        ).add_to(m)

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_birds = birds_near_user[start_index:end_index]

    bird_data = []
    
    for index, bird in enumerate(paginated_birds):
        bird_name = bird.get('comName')

        formatted_bird_name = formatBirdName(bird_name)
        image_url = getWikipediaImage(formatted_bird_name)
        description = f"{bird_name} spotted near your location."

        bird_data.append({
            'imageUrl': image_url,
            'title': bird_name,
            'description': description,
            'url': f'/bird/{quote(bird_name)}'
        })

    # Get HTML of map
    map_html = m._repr_html_()

    return jsonify(mapHtml=map_html, birdData=bird_data)

def getRecentBirds(latitude, longitude):
    headers = {
        'X-eBirdApiToken': EBIRD_API_KEY
    }
    params = {
        'lat': latitude,
        'lng': longitude,
        'dist': 30  #Distance in km for observations
    }
    response = requests.get(EBIRD_API_RECENT_BIRDS_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return []
    
def formatBirdName(bird_name):
    bird_name = bird_name.replace(' ', '_')

    parts = bird_name.split('_')

    formatted_name = parts[0]

    if len(parts) > 1:
        formatted_name += '_' + '_'.join(part.lower() for part in parts[1:])

    return formatted_name

def getWikipediaImage(bird_name):
    formatted_bird_name = formatBirdName(bird_name)
    search_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={formatted_bird_name}&prop=pageimages&format=json&pithumbsize=500'
    response = requests.get(search_url)

    if response.status_code == 200:
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        for page_id, page in pages.items():
            image_url = page.get('thumbnail', {}).get('source')
            if image_url:
                return image_url
    else:
        print(f"Failed to fetch data from Wikipedia. Status code: {response.status_code}")

    return None

def get_bird_info(bird_name):
    return {
        'imageUrl': getWikipediaImage(bird_name),
        'title': bird_name
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
                raise ValidationError("Invalid username or email.")        
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

    selected_id = db.session.scalars(select(User.userID).where(User.username == profile_id)).first()
    if selected_id != None:
        current_profile = db.session.get(User, selected_id)


    # POST happens on "edit profile" submit
    if request.method == 'POST' and "edit_profile_name" in request.form:
        
        new_name = request.form["edit_profile_name"]
        
        try:
            # try to get the current profile from the DB based on username
            if selected_id != None and selected_id == current_user.userID:
                current_profile.firstName = new_name

                db.session.commit()
                return redirect(profile_id)
            else:
                return redirect(profile_id)
        #any additional errors
        except Exception as error:
            print(error)
            return "There was an issue editing your profile"

    # POST happens on Add Photo submit button
    elif request.method == 'POST' and "add_photo_caption" in request.form:
        
        new_caption = request.form["add_photo_caption"]

        #add the new post to the database
        try:
            # try to get the current user from the DB based on username
            if selected_id != None and selected_id == current_user.userID:

                # setting up & adding the post
                new_postID = uuid.uuid4()
                new_post = Post(postID=new_postID, caption=new_caption, datePosted=datetime.now(), userID=selected_id)
                db.session.add(new_post)

                #handle the image upload
                image = request.files["image_file_bytes"]
                filename = secure_filename(image.filename)

                # check to see if the filename exists in the database
                matching_name = db.session.scalars(select(Image).where(Image.name == filename))
                if matching_name != None:
                    #add a unique ID to the start in case it already exists
                    unique_str = str(uuid.uuid4())[:8]
                    image.filename = f"{unique_str}_{image.filename}"
                
                # upload image
                filename = secure_filename(image.filename)
                if filename:
                    file_ext = os.path.splitext(filename)[1]

                    #check that the extension is valid
                    if file_ext not in app.config["UPLOAD_EXTENSIONS"] or file_ext != validate_image(image.stream):
                        return {"error": "File type not supported"}, 400
                    
                    # save it & create the DB object
                    image.save(os.path.join(app.config["UPLOAD_PATH"], filename))
                    imgPath = app.config["UPLOAD_PATH"] + "/" + filename
                    dbImg = PostImage(imageID=uuid.uuid4(), postID=new_postID, name=filename, imagePath=imgPath)
                    db.session.add(dbImg)
                
                
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

    # page is loaded normally
    else:

        if selected_id != None:
            user = db.session.get(User, selected_id)
            posts = user.to_dict()['posts']
            print(posts[0]["images"][0]["imagePath"])

            logged_in = current_user.username == profile_id  #if the logged_in user is viewing their own profile
            context = {
                "socialPosts": socialPosts,
                #"events": events,
                "badges": badges,
                "id" : profile_id,
                "user": user,
                "loggedIn": logged_in,
                "userPosts": posts
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


@app.route('/create_event', methods=['POST', 'GET'])
def create_event():

    #print(f"user id: ")
    #print(current_user.userID)

    if not current_user.is_authenticated: #identify loggedin/loggedout users 
        print(f"Not logged in")
        return jsonify({'success': False, 'message': 'Event not created, not logged in.'})
    
    #print(f"logged in!")
    print(f"user id: ")
    print(current_user.userID)

    data = request.json

    title = data.get('title')
    description = data.get('description')
    creator =  current_user.userID 
    location = data.get('location')
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
        )
    db.session.add(new_event)
    db.session.commit()
        
    return jsonify({'success': True, 'message': 'Event created successfully!'})
   
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
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Event removed from favorites successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Event not found in favorites'})

  
@app.route('/social')
def social():     
    # Query to get all events
    tempEvents = db.session.execute(select(Event)).scalars().all()  
    serialized_events = [event.to_dict() for event in tempEvents]

    #signout to test functionality
    #signout()

    return render_template('social.html', events=serialized_events)

@app.route('/bird')
def bird():
    return render_template("bird.html")

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
if __name__ == "__main__":
    app.run(debug=True)