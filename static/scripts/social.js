
window.onload = onLoad;

function onLoad() {
    getLocation();
}

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(sendLocation);
    
    } else {
        console.log("Geolocation is not supported by this browser.");
    }
}

function handleError(error) {
    console.error('Geolocation error:', error);
    alert('Unable to retrieve your location. Please enter it manually.');
}

function sendLocation(position) {
    latitude = position.coords.latitude;
    longitude = position.coords.longitude;

    console.log("sending location")
    console.log(latitude)
    console.log(longitude)

    if (latitude && longitude) {
        fetch('/social_location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latitude: latitude,
                longitude: longitude
            })
        })
        .then(response => response.json())
        .then(filteredEvents => {
            console.log('Filtered events received:', filteredEvents);
            updateEventList(filteredEvents);
        })
        .catch(error => console.error('Error with location:', error));
    } else {
        console.log('Location data not available.');
    }
}


function updateEventList(events) {
    console.log("updating Events");
    const eventHolder = document.getElementById('event_holder');
    
    let htmlContent = '';
    
    events.forEach((event, index) => {
        const imageFile = `bird${(index % 4) + 1}.jpg`;  // Replace with logic for images
        
        htmlContent += `
            <div class="event_img_details">
                <div class="event-image-container">
                    <img src='../static/images/${imageFile}' alt="${event.title}" class="event-image" />
                </div>
                <div class="event-details">
                    <h4>${event.title}</h4>
                    <span class="favorite-icon" EventID="${event.eventID}"></span>
                    <p>${event.eventDate}</p>
                    <p>${event.location}</p>
                    <p style="margin-top:10px">${event.description}</p>
                    </br>
                </div>
            </div>
        `;
    });

    // Set the generated HTML to the event holder
    eventHolder.innerHTML = htmlContent;

    rebindFavoriteIcons();
}