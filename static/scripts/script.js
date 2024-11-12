document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
    const toggleLocation = document.getElementById('toggle-location');
    
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            toggleLocation.checked = false;
            getCoordinates(this.value);
        }
    });

    document.getElementById('toggle-location').addEventListener('change', function() {
        if (this.checked) {
            getLocation(); 
            document.getElementById('search-input').value = ''; 
        } else {
            if (!userLatitude || !userLongitude) {
                alert("Unable to display map without a valid location.");
            }
        }
    });
});

let bird_data = [];

window.onload = onLoad;

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

let userLatitude = null;
let userLongitude = null;

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(storePosition);
        const toggleLocation = document.getElementById('toggle-location');
        toggleLocation.checked = true;
    
    } else {
        console.log("Geolocation is not supported by this browser.");
    }
}

function handleError(error) {
    console.error('Geolocation error:', error);
    alert('Unable to retrieve your location. Please enter it manually.');
}

function getCoordinates(address) {
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${googleMapsApiKey}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'OK') {
                userLatitude = data.results[0].geometry.location.lat;
                userLongitude = data.results[0].geometry.location.lng;
                processLocation(userLatitude, userLongitude);
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

function createRectangles() {
    const scrollableList = document.getElementById('scrollableList');
    
    scrollableList.innerHTML = '';

    bird_data.forEach(rect => {
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
    if (!userLatitude || !userLongitude) {
        alert("Unable to retrieve location. Please try again.");
        return;
    }

    const url = `https://api.ebird.org/v2/data/obs/geo/recent/${speciesCode}?lat=${userLatitude}&lng=${userLongitude}`;
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
                    userLatitude: userLatitude,
                    userLongitude: userLongitude
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


