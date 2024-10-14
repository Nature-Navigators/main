document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
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

function createRectangles() {
    const scrollableList = document.getElementById('scrollableList');
    
    scrollableList.innerHTML = '';

    bird_data.forEach(rect => {
        const rectangle = document.createElement('div');
        rectangle.className = 'rectangle'; 

        const img = document.createElement('img');
        img.src = rect.imageUrl;
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
            processLocation(userLatitude, userLongitude);
        }
    };
    
    const nextButton = document.createElement('button');
    nextButton.innerText = 'Next';
    nextButton.onclick = () => {
        currentPage++;
        processLocation(userLatitude, userLongitude);
    };

    paginationContainer.appendChild(prevButton);
    paginationContainer.appendChild(nextButton);
}