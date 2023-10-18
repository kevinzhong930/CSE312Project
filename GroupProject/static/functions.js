//This object represents a post and contains 
//the username of the sender, the title of the post, the description of the post, and a unique identifier for the post.
//postJSON: A JavaScript object with properties username, title, description, and id.
const socket = io.connect('http://localhost:8080/');
socket.on('new_post', function(data) {
    addPost(data);
});

function postHTML(postJSON) {
    const username = postJSON.username;
    const title = postJSON.title;
    const description = postJSON.description;
    const postId = postJSON.id;

    //<br>: Inserts a line break. This ensures that each post appears on a new line.

    //>X</button> This is an HTML button. \
    //The text inside the button is "X", suggesting that it's a "delete" button.

    let postHTML = "<br><span id='post_" + postId + "'>";

    //Display the username in bold.
    postHTML += "<b>" + username + "</b>: ";

    //Display the title in bold and with some formatting.
    postHTML += "<strong>Title:</strong> " + title + "<br>";

    //Display the description.
    postHTML += "<strong>Description:</strong> " + description;

    postHTML += "</span>";

    return postHTML;
}

function clearPost() {
    const posts = document.getElementById("postHistory");
    posts.innerHTML = "";
}

function addPost(postJSON) {
    //This element presumably contains all the posts on the webpage.
    const posts = document.getElementById("postHistory");
    //Append the new post to the existing content inside the "postHistory" element
    //postHTML converts postJSON object into a formatted HTML string.
    posts.innerHTML += postHTML(postJSON);
    //Scroll to the top
    posts.scrollIntoView(true);
    posts.scrollTop = 0;
}

//Send a post from the client side to the server.
function sendPost() {
    //Retrieve the title and description input values
    const postTitleBox = document.getElementById("post-title-box");
    const postDescriptionBox = document.getElementById("post-description-box");
    const title = postTitleBox.value;
    const description = postDescriptionBox.value;
    const xsrfToken = document.getElementById("xsrf-token");
    //After retrieving the post, the text box is cleared so the user can type a new title and description.
    postTitleBox.value = "";
    postDescriptionBox.value = "";
    socket.emit('submit_post', { title: title, description: description });
    postTitleBox.focus();
}

//Fetch the latest post history from the server and display it on the client side. 
function updatePost() {
    //Allow the function to make an asynchronous request to the server.
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            //Remove all current post from the display, in preparation for displaying the new post.
            clearPost();
            const posts = JSON.parse(this.response);
            //This loop iterates over each post in the parsed posts array. 
            //For each post, the addPost function is called to display it on the client side.
            for (const post of posts) {
                addPost(post);
            }
        }
    }
    request.open("GET", "/post-history");
    request.send();
}

//Adding a like
function likePost(postId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    request.open("POST", "/post-likes" + postId);
    request.send();
}

function welcome() {
    document.addEventListener("keypress", function (event) {
        if (event.code === "Enter") {
            sendPost();
        }
    });

    document.getElementById("post-title-box").focus();
    setInterval(updatePost, 2000)
    //updatePost()
}