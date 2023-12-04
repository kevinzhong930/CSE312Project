import bcrypt
import secrets
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, make_response, escape, jsonify, abort
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from PIL import Image
import os
import threading
from flask_socketio import SocketIO, send, emit
import json
from flask_mail import Mail, Message
import uuid
import time
from itsdangerous import SignatureExpired
from itsdangerous import URLSafeTimedSerializer
from config import setVar
from flask_limiter.util import get_remote_address
#Resource:
#1. https://realpython.com/handling-email-confirmation-in-flask/
#2. https://www.freecodecamp.org/news/setup-email-verification-in-flask-app/
#3. https://realpython.com/handling-email-confirmation-in-flask/#send-email

app = Flask(__name__)

socketio = SocketIO(app,logger=True, cors_allowed_origins="*")

connections=[]

request_count = {}
limit = 50
time_window = 10
blocked_ips = {}

client = MongoClient("mongodb://mongo:27017/")

db = client["database"]         
#Stores usernames and passwords {'username': username_val, 'password': password_val , 'salt': salt_val} 
user_db = db["user_db"]                             
#Stores authentication tokens {'token': token_val, 'username': username_val}
auth_tokens = db["auth_tokens"]   
#Stores Post History {postId,username,title,description,answer,image}
post_collection = db["post_collection"]
#Stores Grades {username,title,description,user_answer,expected_answer,score}
grade_collection = db["grade_collection"]
#Store all answers submitted for a question until timer for question is up. 
answerStorage = {}
connections=[]

app.secret_key = "secret_Key"
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
setVar()
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)  

@app.route('/') 
def index():
    return render_template('index.html')

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

@app.route('/get-username')
#Displays username
def getUsername():
    token = request.cookies.get('auth_token')
    t = None
    for userInfo in auth_tokens.find({}):
        if token:
            if bcrypt.checkpw(token.encode('utf-8'),userInfo['token']):
                t = userInfo
        else:
            current_username = None
    if t:
        current_username = t['username']
        user = user_db.find_one({'username': current_username})
        verified = False
        if user['verified']:
            verified = True
        return jsonify({'username': t['username'], 'verified': verified})
    return jsonify({'username': None})

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        #HTML injection, escape all HTML characters in the username.
        user_name = escape(request.form['username']) #email
        password = request.form['password']
        #Check if a user name is already exists
        existing_user = user_db.find_one({'username': user_name})
        #Check username and password are filled
        if not user_name or not password:
            return "Username or password cannot be empty", 400
        #Notify if the username is already taken
        if existing_user:
            return "Username already exists.", 400
        #Add user to database
        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(password.encode('utf-8'), salt)
        token = serializer.dumps(user_name, salt='email-confirm')
        user_db.insert_one({'username': user_name, 'password': hash_pass, 'verified': False})
        #Send verification email
        message = Message('Confirm Your Email', sender=os.environ.get('MAIL_USERNAME'), recipients=[user_name])
        link = url_for('confirm_email', token=token, _external=True)
        message.body = 'Your link is {}'.format(link)
        mail.send(message)
        response = make_response(render_template('register.html'))
        return response
    return render_template('index.html')  

def confirm_token(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
        return email
    except Exception:
        return False
    
@app.route('/confirm_email/<token>')
def confirm_email(token):
    email = confirm_token(token)
    print("129 email", email)
    if email:
        document = user_db.find_one({'username': email})
        if document:
            verify = document.get("verified")
            if verify == False:
                user_db.update_one({'username': email}, { '$set': {'verified': True}})
                return "Email successfully verified."
            elif verify == True:
                return "Email is already verified."
        else:
            return "User not found."

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        username = request.form['username']
        password = request.form['password']
        user_data = user_db.find_one({"username": username})
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
                raise Exception()
        else:
            response = "Username does not exist."
            raise Exception()
    except Exception:
        return response, 400

@app.route('/post-history')
def post_history():
    posts = list(post_collection.find({}))
    for post in posts:
        post['_id'] = str(post['_id'])
    return jsonify(posts)

class PostForm(FlaskForm):
    image = FileField('Image', validators=[FileRequired()])

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
    
@app.route('/save-image-websocket', methods=['POST'])
def save_image_websocket():
    id = secrets.token_hex(32)
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            image_path = save_image(image, id)
            return jsonify({'image_path': image_path, 'questionId':id})
    return jsonify({'image_path': "", 'questionId': id})

@app.route('/my-scores')
def my_scores():
    token = request.cookies.get('auth_token')
    t = None
    for userInfo in auth_tokens.find({}):
        if token:
            if bcrypt.checkpw(token.encode('utf-8'),userInfo['token']):
                t = userInfo
        else:
            current_username = None
    if t:
        current_username = t['username']
    else: 
        current_username = None

    grades = list(grade_collection.find({"username":current_username}))
    attempts = len(grades)
    corrects = len([grade for grade in grades if grade['score'] == 1])
    return render_template('my_scores.html', grades_list = grades, attempts = attempts, corrects = corrects)

@app.route('/my-questions')
def my_questions():
    token = request.cookies.get('auth_token')
    t = None
    for userInfo in auth_tokens.find({}):
        if token:
            if bcrypt.checkpw(token.encode('utf-8'),userInfo['token']):
                t = userInfo
        else:
            current_username = None
    if t:
        current_username = t['username']
    else: 
        current_username = None

    grades = list(grade_collection.find({"creater":current_username}))
    grades_by_ids = {}
    for g in grades:
        id = g["question_id"]
        if id not in grades_by_ids:
            grades_by_ids[id] = {'questions': [], 'correct_count': 0, 'attempted_count': 0}

        grades_by_ids[id]['questions'].append(g)
        grades_by_ids[id]['attempted_count'] += 1

        if g['score'] == 1:
            grades_by_ids[id]['correct_count'] += 1
    return render_template('/my_questions.html', grades_list = grades_by_ids)

@app.route('/check')
def check():
    token = request.cookies.get('auth_token')
    t = None
    for userInfo in auth_tokens.find({}):
        if token:
            if bcrypt.checkpw(token.encode('utf-8'),userInfo['token']):
                t = userInfo
        else:
            current_username = None
    if t:
        current_username = t['username']
    else: 
        current_username = None

    postId = request.args.get('postId')
    postInfo = post_collection.find_one({"_id":postId})

    TimeUp = False
    answered = False
    Owner = False
    if postInfo["timeIsUp"] == "Yes":
        TimeUp = True

    if current_username in postInfo["answered"]:
        answered = True
    else:
        post_collection.update_one({"_id":postId}, { "$push": { "answered": current_username } })

    if postInfo["username"] == current_username:
        Owner = True

    response_data = {
        "answered": answered,
        "owner": Owner,
        "timeUp": TimeUp
    }
    return jsonify(response_data)

@app.errorhandler(429)
def ratelimit_error(e):
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    block_ip(ip_address)
    return "Too Many Requests", 429

def block_ip(ip_address):
    blocked_ips[ip_address] = time.time() + 30

@app.before_request
def limit_requests():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    current_time = time.time()

    request_count[ip_address] = request_count.get(ip_address, [])

    while request_count[ip_address] and request_count[ip_address][0] < current_time - time_window:
        request_count[ip_address].pop(0)

    if len(request_count[ip_address]) >= limit:
        abort(429) 
    
    if ip_address in blocked_ips and blocked_ips[ip_address] > time.time():
        return "Too Many Requests", 429

    request_count[ip_address].append(current_time)

#-----------------------------------------------------WEBSOCKETS--------------------------------------------------------------
@socketio.on("connected")
def sendConnectedMessage():
    print("User has connected!")

#Send time updates to the clients
def timer(questionID):
    duration = 60
    while duration:
        timeLeft = '{:02d} second'.format(duration)
        output = json.dumps({'questionID':questionID, 'timeLeft': timeLeft})
        socketio.emit('timeUpdateForClient', output)
        socketio.sleep(1)
        duration = duration -1
    socketio.emit('timeIsUp', {'message': 'Time is up!','questionID': questionID})

@socketio.on("question_submission")
def handleQuestion(question_JSON):
    #Do Question Parsing
    dict = json.loads(question_JSON) #Dictionary of all Post Form Values
    post_collection.insert_one(dict)
    output = json.dumps(dict)
    emit("question_submission",output,broadcast=True)
    id = dict.get("_id")
    socketio.start_background_task(timer, id)

answerStorage_lock = threading.Lock()
@socketio.on("submitAnswer")
def storeAnswer(postIDAndAnswer):
    dict = json.loads(postIDAndAnswer)
    username = dict['username']
    postID = dict['postId']
    answer = dict['user_answer']
    newDictionary={'username' : username,'postId' : postID, 'user_answer' : answer}

    postInfo = post_collection.find_one({'_id' : postID})
    #Check if the user submitting the answer is the same as the creator of the question
    if username == postInfo.get('username'):
        return
    
    with answerStorage_lock:
        if postID in answerStorage:
            answerStorage[postID].append(newDictionary)
        else:
            answerStorage[postID] = [newDictionary]

@socketio.on("QuestionEnd")
def QuestionEnd(postID):
    post_collection.update_one({'_id' : postID}, { "$set": { "timeIsUp": "Yes" } })

@socketio.on("gradeQuestion")
def gradeQuestion(postID):  # postID should be a string
    with answerStorage_lock:
        if postID not in answerStorage:
            return

        answer_data = answerStorage.pop(postID, [])

    postInfo = post_collection.find_one({'_id' : postID})
    title = postInfo['title']
    description = postInfo['description']
    expectedAnswer = postInfo['answer']
    creater = postInfo['username']
    question_id = postInfo['_id']

    for answer in answer_data:
        user_answer = answer['user_answer']
        score = 0

        try:
            if str(user_answer).isnumeric() and str(expectedAnswer).isnumeric():
                score = 1 if int(user_answer) == int(expectedAnswer) else 0
            else:
                score = 1 if user_answer.strip().lower() == expectedAnswer.strip().lower() else 0
        except ValueError:
            score = 0

        out = {'creater':creater,'username': answer['username'], 'title': title, 'description': description,
               'user_answer': user_answer, 'expected_answer': expectedAnswer, 'score': score,
               'question_id':question_id}
        grade_collection.insert_one(out)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8080)
