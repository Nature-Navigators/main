
function clickFollowerFollowing(following)
{
    let followersHeader = document.getElementById("followersHeader");
    let followingHeader = document.getElementById("followingHeader");

    let followingList = document.getElementById("followingList");
    let followersList = document.getElementById("followersList");

    if(following)
    {
        followersHeader.classList.remove("active");
        followingHeader.classList.add("active");

        followingList.style.display = "block";
        followersList.style.display = "none";
    }
    else
    {
        followersHeader.classList.add("active");
        followingHeader.classList.remove("active");

        followingList.style.display = "none";
        followersList.style.display = "block";

    }

}