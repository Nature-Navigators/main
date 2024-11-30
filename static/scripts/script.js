/*
    This file contains javascript logic for the map page - 
    bird rectangles, search bars, map, toggle, bird data, etc
*/

//Event listener for changes to UI elements (ex. toggle, search bars, etc)
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
    const toggleLocation = document.getElementById('toggle-location');

    const input = document.getElementById('search-input');
    const autocomplete = new google.maps.places.Autocomplete(input, {
        types: ['geocode'],
    });

    //Uses Google's Places API for suggestive locations
    autocomplete.addListener('place_changed', function() {
        const place = autocomplete.getPlace();
        if (place.geometry) {
            searched_latitude = place.geometry.location.lat();
            searched_longitude = place.geometry.location.lng();
            processLocation(searched_latitude, searched_longitude);
            toggleLocation.checked = true;
        }
    });

    document.getElementById('bird-search').addEventListener('input', function(e) {
        const searchQuery = e.target.value.toLowerCase();
        filterBirds(searchQuery);
    });

    document.getElementById('toggle-location').addEventListener('change', function() {
        console.log("toggle changed!");
        processLocation(searched_latitude, searched_longitude);
    });
});

let bird_data = []; //holds species specific bird data 

//hardcoded UF coordinates as default location if user denies location sharing
let userLatitude = 29.6465;
let userLongitude = -82.355659;

//searched location set to the same as user location initially
let searched_latitude = userLatitude;
let searched_longitude = userLongitude;

window.onload = onLoad();

function onLoad() {
    const toggleLocation = document.getElementById('toggle-location'); //'Display All Species' toggle turned on by default
    toggleLocation.checked = true;
    adjustWidth();
    getLocation();
}

//width adjustments for UI elements
function adjustWidth() {
    var sidebarSearch = document.getElementById("sidebar-search"); 
    var searchBox = document.getElementById("search-box");
    var windowWidth = window.innerWidth;
    var newWidth = (windowWidth * 0.30); 
    sidebarSearch.style.width = newWidth + "px"; 
    searchBox.style.width = ((newWidth * 0.9)) + "px"; 
}

window.onresize = adjustWidth;

function getLocation() { //browser requests user geolocation
    navigator.geolocation.getCurrentPosition(storePosition, handleNoLocation);
}

function handleNoLocation() { //if user denies location sharing, default UF location is processed directly
    processLocation(userLatitude, userLongitude)
} 

function storePosition(position) { //if user allows location sharing, get coordinates, store in local storage, and process location
    userLatitude = position.coords.latitude;
    userLongitude = position.coords.longitude;
    searched_latitude = userLatitude;
    searched_longitude = userLongitude;
    localStorage.setItem('userLatitude', userLatitude); 
    localStorage.setItem('userLongitude', userLongitude);
    processLocation(userLatitude, userLongitude);
}

async function fetchLocationData(latitude, longitude) { //Calls update_location in app.py for a new set of coordinates and receives new map + bird data
    try {
        const response = await fetch('/update_location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ latitude, longitude })
        });
        const data = await response.json();
        return {
            mapHtml: data.mapHtml, // The HTML for the map
            birdData: data.birdData // The bird data
        };
    } catch (error) {
        console.error('Error fetching location data:', error);
        return { mapHtml: '', birdData: [] };
    }
}

function processLocation(latitude, longitude) { //Calls above functional for a new set of coordinates and generates new bird rectangles
    console.log("Processing location:", latitude, longitude);
    fetchLocationData(latitude, longitude)
        .then(locationData => {
            document.getElementById('map').innerHTML = locationData.mapHtml; 
            bird_data = locationData.birdData;
            createRectangles();
        })
        .catch(error => {
            console.error("Error loading data:", error);
        });
}

function filterBirds(query) { //processes input in bird search bar on map page and generates new set of bird rectangles
    const filteredBirds = bird_data.filter(bird => 
        bird.title.toLowerCase().includes(query) || 
        bird.description.toLowerCase().includes(query)
    );
    createRectangles(filteredBirds); //update rectangles with filtered data
}


function createRectangles(birdArray) { //function that creates the html elements for bird rectangles and listens for click events in bird rectangles
    const scrollableList = document.getElementById('scrollableList');
    
    scrollableList.innerHTML = '';
    var array = birdArray;
    if(!array){
        array = bird_data;
    }

    array.forEach(rect => { //loop through array of birds and generate rectangle for each bird
        const rectangle = document.createElement('div');
        rectangle.className = 'rectangle'; 

        const img = document.createElement('img');
        img.src = rect.imageUrl ? rect.imageUrl : '../static/images/oop.png';
        img.alt = rect.title;

        const textContainer = document.createElement('div'); 
        textContainer.className = 'text-container';

        const title = document.createElement('h3'); 
        title.textContent = rect.title;

        const text = document.createElement('p');
        text.textContent = rect.description;

        textContainer.appendChild(title);
        textContainer.appendChild(text);
        rectangle.appendChild(img);
        rectangle.appendChild(textContainer); 

        const moreButton = document.createElement('button');
        moreButton.className = 'more-recent-button';
        moreButton.innerText = 'All recent sightings';
        moreButton.onclick = (event) => { //if all recent sightings button is clicked
            event.stopPropagation(); //prevent the rectangle click event
            let toggleLocation = document.getElementById('toggle-location');
            toggleLocation.checked = false;
            fetchAllRecentSightings(rect.speciesCode); //calls function to get new bird data for recent sightings of a given species
        };
        rectangle.appendChild(moreButton);
        
        rectangle.onclick = () => {
            window.open(rect.url, '_blank');
        };

        rectangle.style.cursor = 'pointer';

        scrollableList.appendChild(rectangle);
    });
}

function fetchAllRecentSightings(speciesCode) { //function for "all recent sightings" of a specific bird. takes in a species specific code as paramater
    if (!searched_latitude || !searched_longitude) {
        alert("Unable to retrieve location. Please try again.");
        return;
    }

    //connect to eBird API endpoint for all recent sightings within last 30 days of a specific bird
    const url = `https://api.ebird.org/v2/data/obs/geo/recent/${speciesCode}?lat=${searched_latitude}&lng=${searched_longitude}`;
    const headers = {
        'X-eBirdApiToken': ebirdApiKey
    };

    fetch(url, { headers })
        .then(response => response.json())
        .then(data => {
            console.log("Received bird sightings:", data);
            fetch('/update_map_with_bird_sightings', { //calls function in app.py that updates map with new bird icons for all recent sightings
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    birdSightings: data,  
                    latitude: searched_latitude,
                    longitude: searched_longitude
                })
            })
            .then(response => response.json())
            .then(updatedMap => {
                document.getElementById('map').innerHTML = updatedMap.mapHtml; //updates html of map with returned newly created map
            })
            .catch(error => {
                console.error("Error updating the map:", error);
            });
        })
        .catch(error => {
            console.error("Error fetching recent sightings:", error);
        });
}


