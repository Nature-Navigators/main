// ============================================ EVENTS ===================================================

//set up profile button events
var profileButton = document.querySelector("#clickable_profile");
var editProfileText = profileButton.getElementsByTagName("p")[0];

//mouse events
profileButton.addEventListener("mouseover", ()=> { editProfileText.style.visibility = 'visible'; });
profileButton.addEventListener("mouseout", () => {editProfileText.style.visibility = 'hidden';});

//click events
profileButton.addEventListener("click", () => {
    document.getElementById("edit_profile_popup").style.visibility = 'visible';
    grayOut(true);
})


// ======================================== HIDE / SHOW FUNCTIONS =================================================


function hideProfilePopup() {
    document.getElementById("edit_profile_popup").style.visibility = 'hidden';
    grayOut(false);

}

function showGallery() {
    document.getElementById('gallery').style.display = 'grid';
    document.getElementById('createdEvents').style.display = 'none';
    document.getElementById('savedEvents').style.display = 'none';

    changeBoldedNav(0);
  }



function showCreatedEvents() {
    document.getElementById('createdEvents').style.display = 'block';
    document.getElementById('savedEvents').style.display = 'none';
    document.getElementById('gallery').style.display = 'none';

    changeBoldedNav(1);
}

function showSavedEvents() {
    document.getElementById('savedEvents').style.display = 'block';
    document.getElementById('createdEvents').style.display = 'none';
    document.getElementById('gallery').style.display = 'none';

    changeBoldedNav(2);
}

function showPostPopup() {
    document.getElementById("add_post_popup").style.visibility = 'visible';
    grayOut(true);
}

function hidePostPopup() {
    document.getElementById("add_post_popup").style.visibility = 'hidden';
    grayOut(false);
}

function showDatabasePost(databasePost) {

    var cleanStr = cleanJsonString(databasePost);

    if(databasePost != null && databasePost != "")
    {
        let postJson = JSON.parse(cleanStr);
        let userJson = postJson["user"];
        let postImages = postJson["images"];

        //adjust the post popup's DOM 
        document.getElementById("post_content").innerText = postJson["caption"];

        //set image if there is one
        if(postImages.length > 0)
            document.getElementById("post_image").src = "/uploads/" + postImages[0]['name'];   
        else
            document.getElementById("post_image").src = "../static/images/raven.png";
    
        let date = new Date(Date.parse(postJson["datePosted"]));
        document.getElementById("post-time").innerText = "• " + date.toLocaleDateString();

        //set user who posted the post's details
        document.getElementById("posted-by").innerText = userJson["username"]

        //set profile image
        if(userJson["profileImage"] != null)
            document.getElementById("profile_pic").src = "/uploads/" + userJson["profileImage"]["name"]
        else
            document.getElementById("profile_pic").src = "../static/images/profile-icon.webp";

        document.getElementById("html_postID").value = postJson["postID"];  //invisible value used for deleting
        //make it visible
        document.getElementById("post_popup").style.visibility = 'visible';
        grayOut(true);
    
    }
}

function onFileUpload(files, imgID)
{
    // FileReader support
    
    if (FileReader && files && files.length) {
        var fr = new FileReader();
        fr.onload = function () {
            document.getElementById(imgID).src = fr.result;
        }
        fr.readAsDataURL(files[0]);
    }
    
    // Not supported
    else {
        document.getElementById(imgID).src = "../static/images/green-checkmark-line-icon.png";
    }
}

function deletePost() {
    document.getElementById("confirmation_popup").style.visibility = 'visible';
}
function hideConfirmation() {
    document.getElementById("confirmation_popup").style.visibility = 'hidden';

}

//removes escape characters and turns them into their escaped forms (e.g., a new line becomes \n)
    //so JSON.parse doesn't get mad
function cleanJsonString(stringToClean)
{
    let returnStr = stringToClean.replace(/\\+/g, "\\\\");
    returnStr = returnStr.replace(/\n+/g, "\\n");
    returnStr = returnStr.replace(/\t+/g, "\\t");
    returnStr = returnStr.replace(/\/+/g, "\\/");
    
    returnStr = returnStr.replace(/(\b|\f|\r|)*/g, "");
    return returnStr;
}


window.onload = rebindFavoriteIcons()
window.onload = setupEditModal()

function rebindFavoriteIcons() {
    document.querySelectorAll('.favorite-icon').forEach(button => {
        button.addEventListener('click', handleFavoriteClick);
    });
    document.querySelectorAll('.edit-icon').forEach(button => {
        button.addEventListener('click', handleEditClick);
    });
    document.querySelectorAll('.delete-icon').forEach(button => {
        button.addEventListener('click', handleDeleteClick);
    });
}

function handleFavoriteClick(event) {
    const button = event.target;
    const eventID = button.getAttribute('EventID'); // Get the event ID from the button's data attribute
    const isFavorited = button.classList.contains('favorited');

    if (!isFavorited){
        button.classList.add('favorited'); //prematurely show favorited
        fetch('/favorite_event', {
            method: 'POST',
            body: JSON.stringify({ eventID: eventID }),
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => {
            if (response.status === 401) { //specific error code for user not being logged in
                alert("You need to log in to favorite events.");
                button.classList.remove('favorited');
                return null;
            }
            return response.json();
        })
        .then(data => {
            if(data){
                if (data.success) {
                    console.log("Event favorited successfully!");
                }
                else{
                    console.log("There was an issue with favoriting the event.");
                    button.classList.remove('favorited');  //reset the heart if favoriting was not possible
                    console.log(data.message);
                }
            }
        })
        .catch(error => {
            button.classList.remove('favorited');
            console.error('Error favoriting event:', error);
        });
    }
    else {
        button.classList.remove('favorited');
        fetch('/unfavorite_event', {
            method: 'POST',
            body: JSON.stringify({ eventID: eventID }),
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => {
            if (response.status === 401) {
                alert("You need to log in to unfavorite events.");
                button.classList.remove('favorited');
                return null;
            }
            return response.json();
        })
        .then(data => {
            if(data){
                if (data.success) {
                    console.log("Event removed from favorites successfully");
                    button.closest('.event_img_details').remove();
                }
                else{
                    console.log("There was an issue with unfavoriting the event.");
                    button.classList.add('favorited'); //undo the heart being reset, i.e fill heart
                    console.log(data.message);
                }
            }
        })
        .catch(error => {
            button.classList.add('favorited');
            console.error('Error unfavoriting event:', error);
        });
    }
}

//for drag drop image
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("image-input");

dropZone.addEventListener("click", () => {
    fileInput.click();
});

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    handleFiles(files);
});

//recognizes when a new image is added to the dropzone
fileInput.addEventListener("change", (e) => {
    const files = e.target.files;
    handleFiles(files);
});

const closeModal = document.getElementById('closeModal');

// Close modal when clicking close btn
closeModal.addEventListener('click', () => {
    hideEditEventPopup();
    if (fileInput) {
        fileInput.value = ""; // Reset the file input
    }
});

//if user clicks outside modal
const modal = document.getElementById('editModal');
window.addEventListener('click', (event) => {
    if (event.target === modal) {
        hideEditEventPopup();
        if (fileInput) {
            fileInput.value = ""; // Reset the file input
        }
    }
});

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.createElement("img"); //create new image element to save and preview the uploaded image 
                preview.src = e.target.result;
                preview.alt = file.name;
                preview.style.maxWidth = "100%";
                preview.id = "uploaded-image"
                dropZone.innerHTML = ""; // clear drop zone
                dropZone.appendChild(preview);
            };
            reader.readAsDataURL(file);  //converts file's binary and base64 data to a data:image format to send to server
        } else {
            alert("Please upload a valid image file.");
        }
    }
}

function clearImagePreview() {
    const dropZone = document.getElementById("drop-zone");
    //reset dropzone to show default/empty drop box area
    dropZone.innerHTML = `<img style="width:100px" src="../static/images/upload_image.png">
                            <br>
                            <p class="modal-label">Drag & Drop an Image or Click to Upload</p>
                            <input type="file" name="image-input" id="image-input" accept="image/*" style="display: none;">`;
}

function handleEditClick(event) {
    const button = event.target;
    const eventID = button.getAttribute('EventID'); 
    clearImagePreview();

    fetch(`/get_event_details/${eventID}`)  // route to get event details
        .then(response => response.json())
        .then(data => {
            document.getElementById('eventID').value = data.eventID;
            document.getElementById('title').value = data.title;
            document.getElementById('eventDate').value = data.eventDate.split('T')[0];
            document.getElementById('time').value = data.eventDate.split('T')[1].substring(0, 5);
            document.getElementById('location').value = data.location;
            document.getElementById('description').value = data.description;

            if (data.imagePath) {
                const preview = document.createElement("img");
                preview.src = "../" +data.imagePath;  // Use the correct path from event data
                console.log("preview");
                console.log(preview.src);
                preview.alt = data.imageName;  // Assuming imageName is provided
                preview.style.maxWidth = "100%";
                preview.id = "uploaded-image";

                // Clear any existing image in the drop zone and append the preview to display to user
                dropZone.innerHTML = "";
                dropZone.appendChild(preview);
            }

            document.getElementById('editModal').style.visibility = 'visible';

        });

    showEventModal(); //display modal with event data
}

function handleDeleteClick(event) {
    const button = event.target;
    const eventID = button.getAttribute('EventID'); 

    if (confirm('Are you sure you want to delete this event?')) {
        fetch('/delete_event', {
            method: 'POST',
            body: JSON.stringify({ eventID: eventID }),
            headers: { 'Content-Type': 'application/json' } //only eventId needed to find and delete event in db
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Event deleted successfully!");
                location.reload();
            } else {
                console.log("There was an issue deleting the event.");
                console.log(data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting event:', error);
        });
    }
}

function hideSocialPost() {
    document.getElementById("post_popup").style.visibility = 'hidden';
    grayOut(false);

}

function showFollowerPopup()
{
    document.getElementById("follower_popup").style.visibility = 'visible';
    grayOut(true);

}
function hideFollowerPopup() {

    document.getElementById("follower_popup").style.visibility = 'hidden';
    grayOut(false);
}


// determines if the background of the screen should be darker (for popups to "pop" visually)
function grayOut(shouldGray)
{
    if(shouldGray)
    {
        document.getElementById('gray_out').style.visibility = 'visible';
        document.getElementsByTagName('body')[0].style.setProperty('overflow-y', 'hidden');


    }
    else
    {
        document.getElementById('gray_out').style.visibility = 'hidden';
        document.getElementsByTagName('body')[0].style.setProperty('overflow-y', 'scroll');

    }
}

// determines which header (e.g., "Saved Events," "Created Events") should be bolded
function changeBoldedNav(boldIndex)
{
    let column = document.getElementById('mini_nav');

    //loop the nav bar elements
    let elements = column.getElementsByTagName('li');
    for(let i = 0; i < elements.length; i++)
    {
        //the style of the current li's a tag
        let style = elements[i].getElementsByTagName("a")[0].style;

        //bold it when selected
        if(i == boldIndex)
        {
            style.setProperty("font-weight", "600");
            style.setProperty("color", "#1d1d1d");
        }
        //set it to normal
        else
        {
            style.setProperty("font-weight", "400");
            style.setProperty("color", "#818181");

        }
    }

}

// For location dropdown
const locationInput = document.getElementById('location');
const cityList = document.getElementById('cityList');

// Debounce function to limit API calls
let debounceTimeout;
const debounce = (func, delay) => {
    clearTimeout(debounceTimeout); // Clear the previous timeout
    // set new timeout if prev time out was interrupted 
    debounceTimeout = setTimeout(func, delay); 
};

// Add event listener to the location input field
locationInput.addEventListener('input', () => {
    debounce(() => {
        const query = locationInput.value.trim(); // Get the trimmed input value
        if (query.length < 2) return; // Don't search before 2 chars typed

        const username = "{{g.geo_user}}"; //get username for geonames from .env

        // Fetch cities matching the input
        fetch(`http://api.geonames.org/searchJSON?formatted=true&q=${query}&maxRows=40&lang=en&username=${username}`)
            .then(response => response.json())
            .then(data => {
                cityList.innerHTML = ''; // Clear previous options

                data.geonames.forEach(place => {
                    const cityName = place.name;
                    const country = place.countryName;
                    const state = place.adminName1 || ''; // 'adminName1' holds the state/region

                    const option = document.createElement('option');
                    option.value = `${cityName}, ${state ? state + ', ' : ''}${country}`; //format entry for display
                    option.textContent = option.value;
                    cityList.appendChild(option); // Append the option to the city list
                });
            })
            .catch(error => console.error('Error fetching cities:', error));  // Log any errors
    }, 50); // Delay of 50 milliseconds
});

function setupEditModal(){
    const editForm = document.getElementById('editForm');
    editForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const formData = new FormData(editForm);
        
        const fileInput = document.getElementById("uploaded-image"); //retrives image element created when the user uploads an image to the dropzone

        const eventData = {
            image: fileInput && fileInput.src ? fileInput.src : undefined,
            imageName:fileInput && fileInput.alt ? fileInput.alt : undefined, //image alt holds the name of the image file
            eventID : formData.get('eventID'),
            title: formData.get('title'),
            eventDate: formData.get('eventDate'),
            time: formData.get('time'),
            location: formData.get('location'),
            description: formData.get('description'),
        };

        fetch('/edit_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Event updated successfully!');
                location.reload(); 
            } else {
                console.error('Error updating event:', data.message);
            }
        });
    });

    hideEditEventPopup();
}

function showEventModal(){
    document.getElementById("editModal").style.visibility = 'visible';
    grayOut(true);

}

function hideEditEventPopup() {
    document.getElementById('editModal').style.visibility = 'hidden';
    grayOut(false);
}