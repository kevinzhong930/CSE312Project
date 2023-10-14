//Creating the HTML for each Post
function postHTML(postJSON) {
    const username = postJSON.username;
    const title = postJSON.title;
    const description = postJSON.description;
    const postId = postJSON.id;

    
    let postHTML = "<br><span id='post_" + postId + "'>";

    //Display the username in bold.
    postHTML += "<b>" + username + "</b>: ";

    //Display the title in bold and with some formatting.
    postHTML += "<strong>Title:</strong> " + title + "<br>";

    //Display the description.
    postHTML += "<strong>Description:</strong> " + description;

    //Display the Like/Dislike Buttons
    postHTML += "<button onclick='likePost(\"" + postId + "\")'>LIKE</button> <button onclick='dislikePost(\"" + postId + "\")'>DISLIKE</button>"

    postHTML += "</span>";

    return postHTML;

}

//Adding a like
function likePost(postId) {
    return 
}

//Adding a dislike
function dislikePost(postId) {
    return
}

function addMessageToPosts(messageJSON) {
    const posts = document.getElementById("postHistory");
    posts.innerHTML += postHTML(messageJSON);
}

function updatePosts() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const posts = JSON.parse(this.response);
            for (const post of posts) {
                addMessageToPosts(post);
            }
        }
    }

    request.open("GET", "/post-history");
    request.send();
}

function welcome() {
    updatePosts();
    setInterval(updatePosts,2000)
}
