from flask import Flask, render_template, url_for, redirect
# from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Email, InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer as Serializer
from db_models import db, User, Post

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '4a0a3f65e0186d76a7cef61dd1a4ee7b'
db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class SignUpForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})  
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), Length(min=4, max=20), EqualTo('password')], render_kw={"placeholder": "Confirm_Password"})
    submit = SubmitField("Sign Up")

def validate_username(self, username):
    exists_user = User.query.filter_by(username=username.data).first()
    if exists_user:
        raise ValidationError("Username already exists. Select a new username.")

def validate_email(self, email):
    exists_email = User.query.filter_by(email=email.data).first()
    if exists_email:
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
        exists_user = User.query.filter_by(
            username=username.data).first()
        if not exists_user:
            raise ValidationError("Username does not exist.")
    
    def validate_email(self, email):
        exists_email = User.query.filter_by(email=email.data).first()
        if not exists_email:
            raise ValidationError("Email does not exist.")
        
    
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/map')
def map():
    return render_template("map.html")

@app.route('/signin', methods=['GET','POST'])
def signin():
    form = SignInForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data, email=form.email.data).first()
            if user:
                if not bcrypt.check_password_hash(user.password, form.password.data):
                    raise ValidationError("Incorrect password.")
                else:
                    login_user(user)
                    return redirect(url_for('profile'))
            else:
                raise ValidationError("Invalid username or email.")
        except ValidationError as e:
            form.username.errors.append(e.args[0])  
            return render_template("signin.html", form=form)
    return render_template("signin.html", form=form)


def signout():
    logout_user()
    return redirect(url_for('signin'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        hashed_passwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(email=form.email.data, username=form.username.data, password=hashed_passwd)
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('signin'))
    return render_template("signup.html", form=form)

@app.route('/profile')
def profile():
    return render_template("profile.html")
@login_required
@app.route('/social')
def social():
    return render_template("social.html")

@app.route('/bird')
def bird():
    return render_template("bird.html")

if __name__ == "__main__":
    app.run(debug=True)