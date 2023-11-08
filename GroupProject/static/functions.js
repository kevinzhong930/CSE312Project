const ws = true;
let socket = null;

const characters ='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
function generateString(length) {
    let result = ' ';
    const charactersLength = characters.length;
    for ( let i = 0; i < length; i++ ) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}

let postForm = document.getElementById("postSubmission");
postForm.addEventListener("submit", (e) => {
    e.preventDefault();
    let username = document.getElementById("username").innerHTML
    let title = document.getElementById("title");
    let description = document.getElementById("description");
    let image = document.getElementById("image");
    let answer = document.getElementById("open_answer")
    let id = generateString(10);
    if (username !== "") {
        socket.send(JSON.stringify({"username": username, "messageType": "question", "title": title, "description": description, "image_path": image, "answer":answer, "_id": id}))
    }
})

//Establish a WebSocket connection with the server
function initWS() {
    socket = new WebSocket('ws://' + window.location.host + '/websocket');

    //Called whenever data is received from the server over the WebSocket connection
    socket.onmessage = function (ws_message) {
        const message = JSON.parse(ws_message.data);
        const messageType = message.messageType
        if(messageType === 'question'){
            addPostToPosts(message);
        } 
        else if (messageType === 'timer'){
            updateTimer(message.postId, message.timeLeft);
        } 
        else if (messageType === 'lock-question'){
            handleTimerEnd(message.postId);
        }
    }
}

//Creating the HTML for each Post
function postHTML(postJSON) {
    const username = postJSON.username;
    const title = postJSON.title;
    const description = postJSON.description;
    const image = postJSON.image_path
    const postId = postJSON._id;;

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
        postHTML += "<img src='" + image + "' alt='Image' style='max-width: 100%; display: block; margin-bottom: 10px;'>";
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
    if (ws) {
        initWS();
    }
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

//Function to update the timer for each post
function updateTimer(timeLeft) {
    const timerData = document.getElementById('timer');
    if (timerData) {
        timerData.textContent = 'Time left: ' + timeLeft + 's';
    }
}