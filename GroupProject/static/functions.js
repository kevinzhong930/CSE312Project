//Creating the HTML for each Post
function postHTML(postJSON) {
    const username = postJSON.username;
    const title = postJSON.title;
    const description = postJSON.description;
    const postId = postJSON._id;
    const image = postJSON.image_path;
    //const likeCount = getLikes(postId);
    // const likeCount = postJSON.likeCount;

    let postHTML = "<div class='post-box' id='post_" + postId + "'>";

    //Display the username in bold.
    postHTML += "<b>" + username + "</b>: ";

    //Display the title in bold and with some formatting.
    postHTML += "<strong>Title:</strong> " + title + "<br>";

    //Display the description.
    postHTML += "<strong>Description:</strong> " + description;

    postHTML += "<br><br>";

    //Display the Image
    if (image) {
        postHTML += "<img src='" + image + "style='max-width: 100%; display: block; margin-bottom: 10px;'>";
    }
    //Display the Like/Dislike Buttons and the Counter for Likes
    // postHTML +=  likeCount + " likes  " + "<button onclick='likePost(\"" + postId + "\")'>LIKE</button>" ;

    // Add an input box for the answer.
    postHTML += "<input type='text' placeholder='Enter your answer' id='answer_" + postId + "'><br>";

    // Add a submit button for the answer.
    postHTML += "<button onclick='submitAnswer(\"" + postId + "\")'>Submit Answer</button>";
 
    postHTML += "</div>";

    postHTML += "</div>";

    return postHTML;

}

//Adding a like
function likePost(postId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            //console.log(this.response);
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

function getLikes(postId) {
    const request = new XMLHttpRequest();
    var output = "";
    request.responseType = "string";
    request.onload = () => {
        if (request.readyState == 4 && request.status == 200){
            //const data = request.response;
            output = request.response;
            //return parseInt(data);
            console.log(output);
            return output;
        }
        else{
            console.log("Error getting like count");
        }
    }
    request.open("GET", "/get-likes/" + postId);
    request.send();
    //console.log(output);
    return output;
}

async function getLikes2(postId) {
    const response = await fetch('/get-likes/' + postId)
    const data = await response.json()
    return data;
}