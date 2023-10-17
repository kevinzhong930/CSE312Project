
import bcrypt
import secrets
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, escape, jsonify

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")

db = client["database"]         
app.secret_key = "secret_Key"

# Stores usernames and passwords {'username': username_val, 'password': password_val} 
user_db = db["user_db"]                             

# Stores authentication tokens {'token': token_val, 'username': username_val}
auth_tokens = db["auth_tokens"]     

# Stores Post History {postId,username,title,description,likes}
post_collection = db["post_collection"]

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # HTML injection, escape all HTML characters in the username.
        user_name = escape(request.form['username'])
        password = request.form['password']

        # Check if a user name is already exists
        existing_user = user_db.find_one({'name': user_name})

        # Check username and password are filled
        if not user_name or not password:
            flash('Username or password cannot be empty')
            return redirect(url_for('index'))

        # Notify if the username is already taken
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('index'))

        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(password.encode('utf-8'), salt)

        user_db.insert_one({'name': user_name, 'password': hash_pass, 'salt': salt})
        flash('Registration success')
        return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/') 
def index():
    return render_template('index.html')

@app.route('/get-username')
# Displays username
def getUsername():
    token = request.cookies.get('auth_token')
    t = auth_tokens.find_one({'token': token})
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
        username = request.form['username']
        password = request.form['password']
        user_data = user_db.find_one({"name": username})

        if user_data:
            hashed_PW = bcrypt.hashpw(password.encode('utf-8'), user_data['salt'])
            if hashed_PW == user_data['password']:
                token = secrets.token_hex(32)
                auth_tokens.insert_one({'token': token, 'username': username})
                response = make_response(render_template('login.html'))
                response.set_cookie("auth_token", token, max_age=3600, httponly=True)
                return response
            else:
                response = "Invalid password."
                raise Exception()
        else:
            response = "Username does not exist."
            raise Exception()

    except Exception:
        return response, 400
    
@app.route('/post-history')
def post_history():
    posts = post_collection.find({})
    for post in posts:
        post['_id'] = str(post['_id'])
    return jsonify(posts)

@app.route('/post-likes')
def likeFunction(postId):
    post = post_collection.find({"postId" : postId})
    return

@app.route('/post-submission')
def submitPost():
    username = ""

    if request.cookies['auth_token']:
        auth_token = request.cookies['auth_token']
        for userInfo in user_db.find({}):
            if bcrypt.checkpw(auth_token.encode(),userInfo['auth_token']):
                username = userInfo['username']
                break
        
    else:
        response = "Not Logged In"
        make_response(response)
        return response

    title = request.form['title']
    description = request.form['description']
    post_collection.insert_one({"username" : username,"title" : title, "description" : description, "likes" : 0})
    #Clear the Submission Sheet after and send a message saying Post was sent!
    
    return

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
