from flask import Blueprint, render_template

page = Blueprint('page', __name__, template_folder='templates')

@page.route('/')
def home():
    # landing page
    return render_template('page/signup.html')
    # return "Hello Worldddd"

@page.route('/signup')
def signup():
    return render_template('page/signup.html')

@page.route('/signin')
def signin():
    return render_template('page/signin.html')
