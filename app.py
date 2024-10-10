from flask import Flask, render_template, request, jsonify
import folium
from temp_data import *
# from markupsafe import Markup

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/map')
def map():
    return render_template("map.html")

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']

    #Create Folium map at user's location
    m = folium.Map(location=[latitude, longitude], zoom_start=13)
    folium.Marker([latitude, longitude], tooltip='Your Location').add_to(m)

    #Get HTML of map
    map_html = m._repr_html_()

    #return HTML in JSON format
    return jsonify(mapHtml=map_html)

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