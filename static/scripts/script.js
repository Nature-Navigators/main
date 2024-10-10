document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
});

const rectangles = [
    { 
        imageUrl: 'https://www.birds.cornell.edu/home/wp-content/uploads/2023/09/334289821-Baltimore_Oriole-Matthew_Plante.jpg', 
        title: 'Baltimore Oriole',
        description: 'The Baltimore Oriole is a vibrant songbird known for its striking orange and black plumage. These birds are often found in open woodlands, orchards, and suburban areas during the warmer months.',
        url: '/bird' 
    },
    { 
        imageUrl: 'https://example.com/bird2.jpg', 
        title: 'Bird 2', 
        description: 'Bird 2 description.',
        url: '/bird' 
    },
    { 
        imageUrl: 'https://example.com/bird3.jpg', 
        title: 'Bird 3', 
        description: 'Bird 3 description.',
        url: '/bird' 
    },
    { 
        imageUrl: 'https://example.com/bird4.jpg', 
        title: 'Bird 4', 
        description: 'Bird 4 description.',
        url: '/bird' 
    },
    { 
        imageUrl: 'https://example.com/bird5.jpg', 
        title: 'Bird 5', 
        description: 'Bird 5 description.',
        url: '/bird' 
    },
    { 
        imageUrl: 'https://example.com/bird6.jpg', 
        title: 'Bird 6', 
        description: 'Bird 6 description.',
        url: '/bird' 
    },
];


function createRectangles() {
    const scrollableList = document.getElementById('scrollableList');

    rectangles.forEach(rect => {
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

        // rectangle.onclick = () => {
        //     window.open(rect.url, '_blank'); 
        // };

        rectangle.onclick = () => {
            window.location.href = (rect.url)
        };

        rectangle.style.cursor = 'pointer';

        scrollableList.appendChild(rectangle);
    });
}

window.onload = onLoad;

function onLoad() {
    createRectangles();
    adjustWidth();
    getLocation();
}


function adjustWidth() {
    var sidebarSearch = document.getElementById("sidebar-search");
    var searchBox = document.getElementById("search-box");
    var windowWidth = window.innerWidth;
    var newWidth = (windowWidth*0.30); 
    sidebarSearch.style.width = newWidth+"px"; 
    searchBox.style.width = ((newWidth*0.9))+"px"; 
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
  
// Right now we just store it to use to route map and make API call with lat and long
function storePosition(position) {
    userLatitude = position.coords.latitude;
    userLongitude = position.coords.longitude;
    localStorage.setItem('userLatitude', userLatitude);
    localStorage.setItem('userLongitude', userLongitude);
    processLocation(userLatitude,userLongitude);
    // POPUP JUST TO PROVE IT'S WORKING
    // REMOVE WHEN IMPLEMENTED
    alert(`Latitude: ${userLatitude}, Longitude: ${userLongitude}`);
}

function processLocation(latitude, longitude){
    fetch('/update_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ latitude, longitude })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('map').innerHTML = data.mapHtml;
    })
    .catch(error => console.error('Error:', error));

}