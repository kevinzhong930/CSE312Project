import bcrypt
import secrets
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, escape, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from PIL import Image
import html
import os

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")

db = client["database"]         
app.secret_key = "secret_Key"

# Stores usernames and passwords {'username': username_val, 'password': password_val , 'salt': salt_val} 
user_db = db["user_db"]                             

# Stores authentication tokens {'token': token_val, 'username': username_val}
auth_tokens = db["auth_tokens"]     

# Stores Post History {postId,username,title,description,likes}
post_collection = db["post_collection"]

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        # HTML injection, escape all HTML characters in the username.
        user_name = escape(request.form['username'])
        password = request.form['password']

        # Check if a user name is already exists
        existing_user = user_db.find_one({'name': user_name})

        # Check username and password are filled
        if not user_name or not password:
            return "Username or password cannot be empty", 400

        # Notify if the username is already taken
        if existing_user:
            return "Username already exists.", 400

        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(password.encode('utf-8'), salt)

        user_db.insert_one({'name': user_name, 'password': hash_pass})
  
        response = make_response(render_template('register.html'))
        return response

    return render_template('index.html')    


@app.route('/') 
def index():
    return render_template('index.html')

@app.route('/get-username')
# Displays username
def getUsername():
    token = request.cookies.get('auth_token')
    t = None
    for userInfo in auth_tokens.find({}):
        if bcrypt.checkpw(token.encode('utf-8'),userInfo['token']):
            t = userInfo
    if t:
        current_username = t['username']
    else: 
        current_username = None
    return jsonify({'username': current_username})

@app.route('/static/functions.js')
def functions():
    file = open("static/functions.js",encoding="utf-8")
    file = file.read()
    response = make_response(file)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.mimetype = "text/javascript"
    return response

@app.route('/static/style.css')
def style():
    file = open("static/style.css",encoding="utf-8")
    file = file.read()
    response = make_response(file)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.mimetype = "text/css"
    return response

@app.route('/favicon.ico')
@app.route('/static/favicon.ico')
def favicon():
    file = open("static/favicon.ico","rb")
    file = file.read()
    response = make_response(file)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.mimetype = "image/ico"
    return response

@app.route('/visit-counter')
def cookieCounter():
    if "Cookie" not in request.headers:
        response = make_response("Cookie Number is: 1")
        response.mimetype = "text/plain"
        response.set_cookie(key= "visits", value= "1", max_age= 3600)
        return response
    else:
        splitCookieList = request.headers["Cookie"].split(";")
        visitsString = splitCookieList[0]

        splitVisitsString = visitsString.split("=")
        visitsNum = int(splitVisitsString[-1])
        visitsNum += 1
        visitsNum = str(visitsNum)

        response = make_response("Cookie Number is: " + visitsNum)
        response.set_cookie(key= "visits", value=visitsNum, max_age = 3600)
        return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        print("110")
        username = request.form['username']
        password = request.form['password']
        user_data = user_db.find_one({"name": username})
        print("123")
        if user_data:
            hashed_PW = bcrypt.checkpw(password.encode('utf-8'), user_data['password'])
            if hashed_PW:

                token = secrets.token_hex(32).encode('utf-8')
                hashedToken = bcrypt.hashpw(token, bcrypt.gensalt())

                if auth_tokens.find_one({'username' : username}) == None:
                    auth_tokens.insert_one({'token': hashedToken, 'username': username})
                else:
                    auth_tokens.update_one({'username' : username} , { "$set" : {'token' : hashedToken}})

                response = make_response(render_template('login.html'))
                response.set_cookie("auth_token", token, max_age=3600, httponly=True)
                return response
            else:
                response = "Invalid password."
                print("136")
                raise Exception()
        else:
            response = "Username does not exist."
            print("140")
            raise Exception()

    except Exception:
        return response, 400
    
@app.route('/post-history')
def post_history():
    posts = list(post_collection.find({}))
    for post in posts:
        post['_id'] = str(post['_id'])
    return jsonify(posts)

@app.route('/post-likes/<postId>', methods=['POST'])
def likeFunction(postId):
    print(postId)
    post = post_collection.find_one({"_id" : postId})
    auth_token = request.cookies.get('auth_token')
    username = ''
    if auth_token:
        for token in auth_tokens.find({}):
            if bcrypt.checkpw(auth_token.encode('utf-8'),token['token']):
                username = token['username']
        
        likeHolder = False
        print(post)
        for key in post:
            if key == username:
                likeHolder = True
            
        if likeHolder == True:
            post_collection.update_one(post,{'$set' : {'likeCount' : post['likeCount'] - 1}})
            post = post_collection.find_one({"_id" : postId})
            post_collection.update_one(post,{'$unset' : {username : ""}})
        else:
            post_collection.update_one(post,{'$set' : {username : ""}})

            post_collection.update_one(post,{'$set' : {'likeCount' : post['likeCount'] + 1}})


        return redirect(url_for('index'))


    else:
        response = "Not Logged In"
        make_response(response)
        return response

@app.route('/get-likes/<postId>', methods=['GET'])
def getLikes(postId):
    post = post_collection.find_one({'_id' : postId})
    numOfLikes = len(post) - 4
    numOfLikes = str(numOfLikes)
    make_response(numOfLikes)
    print(numOfLikes)
    #return numOfLikes
    ##################
    return jsonify(numOfLikes)

class PostForm(FlaskForm):
    image = FileField('Image', validators=[FileRequired()])

@app.route('/post-submission', methods=['POST'])
def submitPost():
    username = ""
    document = None
    auth_token = request.cookies.get('auth_token')
    for token in auth_tokens.find({}):
        if bcrypt.checkpw(auth_token.encode('utf-8'), token['token']):
            document = token       
    if document:
        username = document['username']
    else:
        return "Not Logged In", 403
    
    title = request.form.get('title', "")
    description = request.form.get('description', "")
    open_answer = request.form.get('open_answer', "")
    
    # html escape
    title = html.escape(title)
    description = html.escape(description)
    open_answer = html.escape(open_answer)
    
    id = "postID" + secrets.token_hex(32)
    image = request.files['image']
    if image:
        image_path = save_image(image, id)
    else:
        image_path = None
    
    
    post_collection.insert_one({
        "_id": id,
        "username": username,
        "title": title,
        "description": description,
        "answer": open_answer,
        "image_path": image_path,
        "likeCount": 0
    })
    
    # Clear the Submission Sheet after and send a message saying Post was sent!
    flash('Post submitted successfully!')
    return redirect(url_for('index'))

def save_image(image, id):
    image_folder = os.path.join(app.root_path, 'static/images')
    file_extension = os.path.splitext(image.filename)[1]
    filename = secure_filename(id+file_extension)
    image_path = os.path.join(image_folder, filename)
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    try:
        img = Image.open(image.stream)
        img.save(image_path)
        img.close()
        return os.path.join('/static/images', filename)
    except Exception as e:
        print(f"Error occurred during saving image: {str(e)}")
        return None


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)