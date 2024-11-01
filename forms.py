from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Email, Length, ValidationError, EqualTo, DataRequired
from db_models import User, db
from sqlalchemy import select

class SignUpForm(FlaskForm):

        
    email = StringField(
        validators=[DataRequired(message="Please enter your email"), Email(), Length(max=120)], 
        render_kw={"placeholder": "Email"})  
    username = StringField(
        validators=[DataRequired(message="Please enter your username"), Length(min=4, max=20)], 
        render_kw={"placeholder": "Username"})
    password = PasswordField(
        validators=[DataRequired(message="Please enter your password"), Length(min=4, max=20)], 
        render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(
        DataRequired(message="Please confirm your password"), 
        validators=[EqualTo('password', message='Passwords must match')], 
        render_kw={"placeholder": "Confirm Password"})
    
    submit = SubmitField("Sign Up")


    # def validate_username(self, username):
    #     exists_user =  db.session.scalars(select(User.username == username)).first()
    #     #exists_user = User.query.filter_by(username=username.data).first()
    #     if exists_user:
    #         raise ValidationError("Username already exists. Select a new username.")
        
    def validate_username(self, username):
        print(f"Validating username: {username.data}")  # Debug line
        stmt = select(User).where(User.username == username.data)
        exists_user = db.session.execute(stmt).scalars().first()
        print(f"Exists user: {exists_user}")  # Debug line
        if exists_user:
            raise ValidationError("Username already exists. Select a new username.")

    
    # def validate_email(self, email):
    #     exists_email = User.query.filter_by(email=email.data).first()
    #     if exists_email:
    #         raise ValidationError("Email already exists. Use another email address.")
        
class SignInForm(FlaskForm):
    email = StringField(
        validators=[DataRequired(message="Please enter your email"), Email(), Length(max=120)], 
        render_kw={"placeholder": "Email"})  
    username = StringField(
        validators=[DataRequired(message="Please enter your username"), 
        Length(min=4, max=20)], 
        render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[DataRequired(message="Please enter your password"), Length(
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