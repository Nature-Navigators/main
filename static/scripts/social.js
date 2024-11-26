window.onload = onLoad;

function onLoad() {
    getLocation();
    setupLikeButtons();
    persistLikeButtons();
}

function getLocation() {
    navigator.geolocation.getCurrentPosition(
        (position) => {
            sendLocation(position);
        },
        (error) => {
            console.warn("Geolocation failed or denied, using IP-based location as fallback.");
            fetchLocationViaIP(); // IP location is much less accurate, only if geolocation fails.
        },
        {
            timeout: 5000,     
        }
    );
}

function fetchLocationViaIP() {
    fetch('http://ip-api.com/json')
        .then(response => response.json())
        .then(data => {
            const position = {
                coords: {
                    latitude: data.lat,
                    longitude: data.lon
                }
            };
            sendLocation(position);
        })
        .catch(error => console.error('Error fetching IP location:', error));
}

function handleError(error) {
    console.error('Geolocation error:', error);
    alert('Unable to retrieve your location. Please enter it manually.');
}

function sendLocation(position) {
    latitude = position.coords.latitude;
    longitude = position.coords.longitude;

    //endpoint filters events by proximity and returns list
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
            updateEventList(filteredEvents);
        })
        .catch(error => console.error('Error with location:', error));
    } else {
        console.log('Location data not available.');
    }
}


function updateEventList(events) {
    const eventHolder = document.getElementById('event_holder');
    let htmlContent = '';

    //clears html and recreates it with sorted events in order
    events.forEach((event) => {
        const imageFile = event.imagePath ? event.imagePath : `../static/images/raven.png`;
        const defaultclass = event.imagePath ? ``:  `default-image`        
        const formattedDate = formatEventDate(event.eventDate); 
        const fav = event.favorited ? 'favorited' : '';
        
        htmlContent += `
            <div class="event_img_details">
                <div class="event-image-container">
                    <img src='${imageFile}' alt="${event.title}" class="event-image ${defaultclass}" />                </div>
                <div class="event-details">
                    <h4>${event.title}</h4>
                    <span class="favorite-icon ${fav}" EventID="${event.eventID}"></span>
                    <p>${formattedDate}</p>
                    <p>${event.location}</p>
                    <p style="margin-top:10px">${event.description}</p>
                    </br>
                </div>
            </div>
        `;
    });

    // Set the generated HTML to the event holder
    eventHolder.innerHTML = htmlContent;

    rebindFavoriteIcons(); //rebind icons since innerhtml was replaced
    persistLikeButtons(); 
}

function formatEventDate(eventDate) {
    return moment(eventDate).format("MMMM DD, YYYY [at] hh:mm A");  //same format as datetimeformat used in html files
}

function setupLikeButtons() {
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(button => {
        button.addEventListener('click', handleLikeButtonClick);
    });
}

function persistLikeButtons() {
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(button => {
        const postId = button.getAttribute('data-post-id');
        fetch(`/api/posts/${postId}/like/status`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            const icon = button.querySelector('.like-icon');
            icon.src = data.liked ? "/static/images/filled-heart.png" : "/static/images/empty-heart.png";
            icon.width = 20;
            icon.height = 22;
            const likesCountElement = document.querySelector(`#post_likes_${postId}`);
            if (likesCountElement) {
                likesCountElement.textContent = `${data.likes} likes`;
            }
        })
        .catch(error => {
            console.error('Error fetching like status:', error);
        });
    });
}

function handleLikeButtonClick(event) {
    const button = event.currentTarget;
    const postId = button.getAttribute('data-post-id');
    const icon = button.querySelector('.like-icon');

    fetch(`/api/posts/${postId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Error: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.likes !== undefined) {
            icon.src = data.liked ? "/static/images/filled-heart.png" : "/static/images/empty-heart.png";
            icon.width = 20;
            icon.height = 22;
            const likesCountElement = document.querySelector(`#post_likes_${postId}`);
            if (likesCountElement) {
                likesCountElement.textContent = `${data.likes} likes`;
            }
        } else {
            console.error('Error liking post:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
