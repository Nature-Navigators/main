window.onload = onLoad;

function onLoad() {
    // This function is called when the window loads. It initializes the location fetching,
    // sets up the like buttons, and ensures their state is persisted.
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
            enableHighAccuracy: false,
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
    // to make sure likes persist after updating the event list
    rebindFavoriteIcons(); //rebind icons since innerhtml was replaced
}

function formatEventDate(eventDate) {
    return moment(eventDate).format("MMMM DD, YYYY [at] hh:mm A");  //same format as datetimeformat used in html files
}

function setupLikeButtons() {
    // Select all elements with the class 'like-button'
    const likeButtons = document.querySelectorAll('.like-button');
    // Iterate over each like button
    likeButtons.forEach(button => {
        // Add a click event listener to each button
        button.addEventListener('click', handleLikeButtonClick);
    });
}

function persistLikeButtons() {
    // Select all elements with the class 'like-button'
    const likeButtons = document.querySelectorAll('.like-button');

    const postIds = [];
    likeButtons.forEach(button => {
        // Get the post ID from the data attribute
        postIds.push(button.getAttribute('data-post-id'));
    });

    // send one request with all postIDs
    fetch(`/api/posts/like/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({postIds}) //send postIDs to endpoint
    })
    .then(response => response.json())
    .then(data =>{
        likeButtons.forEach(button => {
            const postId = button.getAttribute('data-post-id');
            const postData =data[postId]; // get data for the specific post

            if (postData) {
                const icon = button.querySelector('.like-icon');
                // Set the icon source based on the like status
                icon.src = postData.liked ? "/static/images/filled-heart.png" : "/static/images/empty-heart.png";
                icon.width = 20;
                icon.height = 22;

                // Update the likes count if it exists
                const likesCountElement = document.querySelector(`#post_likes_${postId}`);
                if (likesCountElement) {
                    likesCountElement.textContent = `${postData.likes} likes`;
                }
            }
        });
    })
    .catch(error => {
        // Handle error silently
    });
}

function handleLikeButtonClick(event) {
    // Get the button that was clicked
    const button = event.currentTarget;
    // Get the post ID from the data attribute
    const postId = button.getAttribute('data-post-id');
    // Get the like icon element within the button
    const icon = button.querySelector('.like-icon');

    // Send a POST request to like/unlike the post
    fetch(`/api/posts/${postId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.status === 401) { //specific error code for user not being logged in
            alert("You need to log in to like posts.");
            return null;
        }
        return response.json();
    })
    .then(data => {
        if (data.likes !== undefined) {
            // Update the icon source based on the like status
            icon.src = data.liked ? "/static/images/filled-heart.png" : "/static/images/empty-heart.png";
            icon.width = 20;
            icon.height = 22;
            // Update the likes count element if it exists
            const likesCountElement = document.querySelector(`#post_likes_${postId}`);
            if (likesCountElement) {
                likesCountElement.textContent = `${data.likes} likes`;
            }
        }
    })
    .catch(error => {
        // Handle error silently
    });
}
