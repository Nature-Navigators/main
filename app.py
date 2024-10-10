from flask import Flask, render_template
from temp_data import *
# from markupsafe import Markup

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/map')
def map():
    return render_template("map.html")

@app.route('/signin')
def signin():
    return render_template("signin.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/profile')
def profile():
    context = {
        "socialPosts": socialPosts,
        "events": events,
        "badges": badges
    }
    return render_template("profile.html", **context)

@app.route('/social')
def social():
    return render_template("social.html")

@app.route('/bird')
def bird():
    return render_template("bird.html")

if __name__ == "__main__":
    app.run(debug=True)