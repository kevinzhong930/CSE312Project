//Creating the HTML for each Post
function postHTML(postJSON) {
    const username = postJSON.username;
    const title = postJSON.title;
    const description = postJSON.description;
    const postId = postJSON._id;

    
    let postHTML = "<div class='post-box' id='post_" + postId + "'>";

    //Display the username in bold.
    postHTML += "<b>" + username + "</b>: ";

    //Display the title in bold and with some formatting.
    postHTML += "<strong>Title:</strong> " + title + "<br>";

    //Display the description.
    postHTML += "<strong>Description:</strong> " + description;

    postHTML += "<br><br>"

    //Display the Like/Dislike Buttons and the Counter for Likes
    postHTML += /* "<br>" + likeCounter + */ "<button onclick='likePost(\"" + postId + "\")'>LIKE</button>" 

    postHTML += "</div>";

    return postHTML;

}

//Adding a like
function likePost(postId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    request.open("POST", "/post-likes/" + postId);
    request.send();
}

//Adding the postHTML on indexHTML
function addPostToPosts(messageJSON) {
    const posts = document.getElementById("postHistory");
    posts.innerHTML += postHTML(messageJSON);
}

//Updates all Posts
function updatePosts() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearPosts();
            const posts = JSON.parse(this.response);
            for (const post of posts) {
                addPostToPosts(post);
            }
        }
    }

    request.open("GET", "/post-history");
    request.send();
}

//Clearing Posts
function clearPosts() {
    const posts = document.getElementById("postHistory");
    posts.innerHTML = "";
}

//Constantly Calls updatePosts() on startup
function welcome() {
    updatePosts();
    setInterval(updatePosts,2000);
}