document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
    const toggleLocation = document.getElementById('toggle-location');
    
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            toggleLocation.checked = true;
            getCoordinates(this.value);
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

    document.getElementById('your-location').addEventListener('click', function() {
        console.log("Go to your location button clicked!");
        if(!userLatitude || !userLongitude){
            getLocation();
        }
        else{
            searched_latitude = userLatitude;
            searched_longitude = userLongitude;
            processLocation(userLatitude, userLongitude);
            document.getElementById('search-input').value = '';
        }
    });
});

let bird_data = [];

//UF coords
let userLatitude = 29.6465;
let userLongitude = -82.355659;

let searched_latitude = userLatitude;
let searched_longitude = userLongitude;

window.onload = onLoad();

function onLoad() {
    adjustWidth();
    getLocation();
}

function adjustWidth() {
    var sidebarSearch = document.getElementById("sidebar-search");
    var searchBox = document.getElementById("search-box");
    var windowWidth = window.innerWidth;
    var newWidth = (windowWidth * 0.30); 
    sidebarSearch.style.width = newWidth + "px"; 
    searchBox.style.width = ((newWidth * 0.9)) + "px"; 
}

window.onresize = adjustWidth;

function getLocation() {
    navigator.geolocation.getCurrentPosition(storePosition, handleNoLocation);
}

function handleNoLocation() {
    processLocation(userLatitude, userLongitude)
}

function getCoordinates(address) {
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${googleMapsApiKey}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'OK') {
                const toggleLocation = document.getElementById('toggle-location');
                searched_latitude = data.results[0].geometry.location.lat;
                console.log("searched lat:", searched_latitude);
                searched_longitude = data.results[0].geometry.location.lng;
                if(toggleLocation.checked){
                    processLocation(searched_latitude, searched_longitude);
                }
                else{
                    userLatitude = data.results[0].geometry.location.lat;
                    userLongitude = data.results[0].geometry.location.lng;
                    processLocation(userLatitude, userLongitude);  
                }
            } else {
                console.error('Geocoding failed: ' + data.status);
            }
        })
        .catch(error => console.error('Error:', error));
}

function storePosition(position) {
    userLatitude = position.coords.latitude;
    userLongitude = position.coords.longitude;
    localStorage.setItem('userLatitude', userLatitude);
    localStorage.setItem('userLongitude', userLongitude);
    processLocation(userLatitude, userLongitude);
}

async function fetchLocationData(latitude, longitude) {
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

function processLocation(latitude, longitude) {
    console.log("Processing location:", latitude, longitude);
    fetchLocationData(latitude, longitude)
        .then(locationData => {
            document.getElementById('map').innerHTML = locationData.mapHtml; 
            bird_data = locationData.birdData;
            // searched_latitude = latitude;
            // searched_longitude = longitude; 
            createRectangles();
        })
        .catch(error => {
            console.error("Error loading data:", error);
        });
}

function filterBirds(query) {
    const filteredBirds = bird_data.filter(bird => 
        bird.title.toLowerCase().includes(query) || 
        bird.description.toLowerCase().includes(query)
    );
    createRectangles(filteredBirds); // Update rectangles with filtered data
}


function createRectangles(birdArray) {
    const scrollableList = document.getElementById('scrollableList');
    
    scrollableList.innerHTML = '';
    var array = birdArray;
    if(!array){
        array = bird_data;
    }

    array.forEach(rect => {
        const rectangle = document.createElement('div');
        rectangle.className = 'rectangle'; 

        const img = document.createElement('img');
        // img.src = rect.imageUrl;
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
        moreButton.onclick = (event) => {
            event.stopPropagation(); //prevent the rectangle click event
            let toggleLocation = document.getElementById('toggle-location');
            toggleLocation.checked = false;
            fetchAllRecentSightings(rect.speciesCode);
        };
        rectangle.appendChild(moreButton);

        rectangle.onclick = () => {
            window.location.href = rect.url;
        };

        rectangle.style.cursor = 'pointer';

        scrollableList.appendChild(rectangle);
    });
}

function fetchAllRecentSightings(speciesCode) {
    if (!searched_latitude || !searched_longitude) {
        alert("Unable to retrieve location. Please try again.");
        return;
    }

    const url = `https://api.ebird.org/v2/data/obs/geo/recent/${speciesCode}?lat=${searched_latitude}&lng=${searched_longitude}`;
    const headers = {
        'X-eBirdApiToken': ebirdApiKey
    };

    fetch(url, { headers })
        .then(response => response.json())
        .then(data => {
            console.log("Received bird sightings:", data);
            fetch('/update_map_with_bird_sightings', {
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
                document.getElementById('map').innerHTML = updatedMap.mapHtml;
            })
            .catch(error => {
                console.error("Error updating the map:", error);
            });
        })
        .catch(error => {
            console.error("Error fetching recent sightings:", error);
        });
}


