document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            getCoordinates(this.value);
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
    } else {
        console.log("Geolocation is not supported by this browser.");
    }
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


let currentPage = 1;
const pageSize = 10;

function processLocation(latitude, longitude) {
    currentPage = 1;
    fetch('/update_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ latitude, longitude, page: currentPage, page_size: pageSize })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('map').innerHTML = data.mapHtml;
        bird_data = data.birdData;
        createRectangles();
        updatePagination();
    })
    .catch(error => console.error('Error:', error));
}

function fetchBirdData(latitude, longitude, page) {
    fetch('/update_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ latitude, longitude, page, page_size: pageSize })
    })
    .then(response => response.json())
    .then(data => {
        bird_data = data.birdData;
        createRectangles();
        updatePagination();
    })
    .catch(error => console.error('Error:', error));
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

        rectangle.onclick = () => {
            window.location.href = rect.url;
        };

        rectangle.style.cursor = 'pointer';

        scrollableList.appendChild(rectangle);
    });
}

function updatePagination() {
    const paginationContainer = document.getElementById('pagination');
    paginationContainer.innerHTML = '';

    const prevButton = document.createElement('button');
    prevButton.innerText = 'Previous';
    prevButton.disabled = currentPage === 1;
    prevButton.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            fetchBirdData(userLatitude, userLongitude, currentPage);
        }
    };

    const nextButton = document.createElement('button');
    nextButton.innerText = 'Next';
    nextButton.onclick = () => {
        currentPage++;
        fetchBirdData(userLatitude, userLongitude, currentPage);
    };

    paginationContainer.appendChild(prevButton);
    paginationContainer.appendChild(nextButton);
}