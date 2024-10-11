from flask import Flask, render_template, request, jsonify
import requests
import folium
import os
import xyzservices.providers as xyz #Can use this to change map type
from temp_data import *
# from markupsafe import Markup

app = Flask(__name__)

EBIRD_API_RECENT_BIRDS_URL = 'https://api.ebird.org/v2/data/obs/geo/recent' 
EBIRD_API_KEY = os.environ['EBIRD_API_KEY']

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
    birds_near_user = getRecentBirds(latitude, longitude)

    #Create Folium map at user's location
    m = folium.Map(location=[latitude, longitude], zoom_start=13)
    folium.Marker([latitude, longitude], tooltip='Your Location').add_to(m)

    #Add markers for each bird observation
    for bird in birds_near_user:
        bird_name = bird.get('comName')
        bird_lat = bird.get('lat')
        bird_long = bird.get('lng')
        folium.Marker(
            location=[bird_lat, bird_long],
            tooltip=bird_name,
            icon=folium.Icon(color='red')
        ).add_to(m)

    #Get HTML of map
    map_html = m._repr_html_()

    #return HTML in JSON format
    return jsonify(mapHtml=map_html)

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