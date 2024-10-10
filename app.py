from flask import Flask, render_template, url_for, redirect
# from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Email, InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/nike/Downloads/organized/UF/UF_coursework/SENIOR_PROJ/main/database.db'
app.config['SECRET_KEY'] = 'summakey'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)  
    password = db.Column(db.String(80), nullable=False)


class SignUpForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(max=120)], render_kw={"placeholder": "Email"})  
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
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
    submit = SubmitField("Login")     

    def val_user(self, username):
        exists_user = User.query.filter_by(
            username=username.data).first()
        
        if exists_user(self, username):
            raise ValidationError(
                "Username already exists. Select new username")
    def validate_email(self, email):
        exists_email = User.query.filter_by(email=email.data).first()
        if exists_email:
            raise ValidationError("Email already exists. Use another email address.")
    
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
        hashed_passwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(email=form.email.data, username=form.username.data, password=hashed_passwd)
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template("signin.html", form=form)

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

@app.route('/social')
def social():
    return render_template("social.html")

@app.route('/bird')
def bird():
    return render_template("bird.html")

if __name__ == "__main__":
    app.run(debug=True)