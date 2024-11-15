// ============================================ EVENTS ===================================================

//set up profile button events
var profileButton = document.querySelector("#clickable_profile");
var editProfileText = profileButton.getElementsByTagName("p")[0];

//mouse events
profileButton.addEventListener("mouseover", ()=> { editProfileText.style.visibility = 'visible'; });
profileButton.addEventListener("mouseout", () => {editProfileText.style.visibility = 'hidden';});

//click events
profileButton.addEventListener("click", () => {
    setDefaultEditProfile();
    document.getElementById("edit_profile_popup").style.visibility = 'visible';
    grayOut(true);
})


// ======================================== FUNCTIONS =================================================

//set default profile edit popup values
function setDefaultEditProfile() {
    var profileForm = document.getElementById("edit_profile_form");
    var inputs = profileForm.getElementsByTagName("input");
    inputs[0].value = document.getElementById("name").innerHTML;
    inputs[1].value = document.getElementById("title").innerHTML;

    var bio = profileForm.getElementsByTagName("textarea")[0];
    bio.value = document.querySelector(".content").getElementsByTagName("p")[0].innerText;
}

function saveProfileEdits() {
    var profileForm = document.getElementById("edit_profile_form");
    var inputs = profileForm.getElementsByTagName("input");

    document.getElementById("name").innerText = inputs[0].value;
    document.getElementById("title").innerText = inputs[1].value;

    var bio = profileForm.getElementsByTagName("textarea")[0];
    document.querySelector(".content").getElementsByTagName("p")[0].innerText = bio.value;

    hideProfilePopup();
}

function hideProfilePopup() {
    document.getElementById("edit_profile_popup").style.visibility = 'hidden';
    grayOut(false);

}

function showGallery() {
    document.getElementById('gallery').style.display = 'grid';
    document.getElementById('badges').style.display = 'none';
    document.getElementById('createdEvents').style.display = 'none';
    document.getElementById('savedEvents').style.display = 'none';

    changeBoldedNav(0);
  }


function showBadges() {
    document.getElementById('badges').style.display = 'block';
    document.getElementById('gallery').style.display = 'none';
    document.getElementById('createdEvents').style.display = 'none';
    document.getElementById('savedEvents').style.display = 'none';


    changeBoldedNav(1);
}

function showCreatedEvents() {
    document.getElementById('createdEvents').style.display = 'block';
    document.getElementById('savedEvents').style.display = 'none';
    document.getElementById('gallery').style.display = 'none';
    document.getElementById('badges').style.display = 'none';

    changeBoldedNav(2);
}

function showSavedEvents() {
    document.getElementById('savedEvents').style.display = 'block';
    document.getElementById('createdEvents').style.display = 'none';
    document.getElementById('gallery').style.display = 'none';
    document.getElementById('badges').style.display = 'none';

    changeBoldedNav(3);
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

//TODO: DELETE ME (replaced by showDatabasePost)
function showSocialPost(postString) {

    if(postString != null && postString != "")
    {
        let postJson = JSON.parse(postString);

        //adjust the post popup's DOM 
        document.getElementById("post_image").src = postJson["image"];
        document.getElementById("post_likes").innerText = postJson["likes"] + " likes";
        document.getElementById("post_content").innerText = postJson["content"];

        //make it visible
        document.getElementById("post_popup").style.visibility = 'visible';
        grayOut(true);
    
    }
}

window.onload = rebindFavoriteIcons()

function rebindFavoriteIcons() {
    document.querySelectorAll('.favorite-icon').forEach(button => {
        button.addEventListener('click', handleFavoriteClick);
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
            if (response.status === 401) {
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
                    button.classList.remove('favorited');
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
                    button.classList.add('favorited');
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

function handleDeleteClick(event) {
    const button = event.target;
    const eventID = button.getAttribute('EventID'); 

    if (confirm('Are you sure you want to delete this event?')) {
        fetch('/delete_event', {
            method: 'POST',
            body: JSON.stringify({ eventID: eventID }),
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Event deleted successfully!");
                button.closest('.event_img_details').remove();
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

function showEventPopup(eventString)
{
    if(eventString != null && eventString != "")
    {
        let eventJson = JSON.parse(eventString);
        //adjust the post popup's DOM 
     
        //make it visible
        document.getElementById("event_popup").style.visibility = 'visible';
        grayOut(true);
    
    }
}
function hideEventPopup()
{
    document.getElementById("event_popup").style.visibility = 'hidden';
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
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(func, delay);
};

locationInput.addEventListener('input', () => {
    debounce(() => {
        const query = locationInput.value.trim();
        if (query.length < 2) return; // Don't search before 2 chars typed

        // Fetch cities matching the input
        fetch(`http://api.geonames.org/searchJSON?formatted=true&q=${query}&maxRows=40&lang=en&username=salonikaranth`)
            .then(response => response.json())
            .then(data => {
                cityList.innerHTML = ''; // Clear previous options

                data.geonames.forEach(place => {
                    const cityName = place.name;
                    const country = place.countryName;
                    const state = place.adminName1 || ''; // 'adminName1' holds the state/region

                    const option = document.createElement('option');
                    option.value = `${cityName}, ${state ? state + ', ' : ''}${country}`;
                    option.textContent = option.value;
                    cityList.appendChild(option);
                });
            })
            .catch(error => console.error('Error fetching cities:', error));
    }, 50);
});

