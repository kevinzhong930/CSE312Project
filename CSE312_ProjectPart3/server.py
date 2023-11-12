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
import hashlib
import base64
import time
import threading
from flask_socketio import SocketIO, send, emit
import json
import random
import string

#Resources:
#1. https://www.geeksforgeeks.org/how-to-create-a-countdown-timer-using-python/#
######

app = Flask(__name__)

socketio = SocketIO(app,logger=True)

connections=[]

client = MongoClient("mongodb://mongo:27017/")

db = client["database"]         
app.secret_key = "secret_Key"

#Stores usernames and passwords {'username': username_val, 'password': password_val , 'salt': salt_val} 
user_db = db["user_db"]                             

#Stores authentication tokens {'token': token_val, 'username': username_val}
auth_tokens = db["auth_tokens"]     

#Stores Post History {postId,username,title,description,answer,image}
post_collection = db["post_collection"]

#Stores Grades {username,title,description,user_answer,expected_answer,score}
grade_collection = db["grade_collection"]

answerStorage = {} #Store all answers submitted for a question until timer for question is up. 

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        #HTML injection, escape all HTML characters in the username.
        user_name = escape(request.form['username'])
        password = request.form['password']
        #Check if a user name is already exists
        existing_user = user_db.find_one({'name': user_name})
        #Check username and password are filled
        if not user_name or not password:
            return "Username or password cannot be empty", 400
        #Notify if the username is already taken
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
    print(request.files)
    id = secrets.token_hex(32)
    if 'image' in request.files:
        image = request.files['image']
        print('check1')
        if image.filename != '':
            print('check2')            
            image_path = save_image(image, id)
            return jsonify({'image_path': image_path, 'questionId':id})
    print('check11')
    return jsonify({'image_path': "", 'questionId': id})

#-----------------------------------------------------WEBSOCKETS--------------------------------------------------------------
@socketio.on("connected")
def sendConnectedMessage():
    print("User has connected!")

@socketio.on('hello')
def hello_world(data):
    print('\n\nhello world test\n')
    emit('hello', 'world')

#Send time updates to the clients
def timer(questionID):
    duration = 10
    while duration:
        #print("server.py 244 duration", duration)
        timeLeft = '{:02d} seconds'.format(duration)
        #print("server.py 246 timeLeft", timeLeft)
        output = json.dumps({'questionID':questionID, 'timeLeft': timeLeft})
        socketio.emit('timeUpdateForClient', output)
        #print("After socketio.emit")
        socketio.sleep(1)
        duration = duration -1
    socketio.emit('timeIsUp', {'message': 'Time is up!','questionID': questionID})

@socketio.on("question_submission")
def handleQuestion(question_JSON):
    #Do Question Parsing
    dict = json.loads(question_JSON) #Dictionary of all Post Form Values
    # print(f"adding dict: {dict}")
    post_collection.insert_one(dict)
    output = json.dumps(dict)
    emit("question_submission",output)
    id = dict.get("_id")
    socketio.start_background_task(timer, id)

@socketio.on("submitAnswer")
def storeAnswer(postIDAndAnswer):
    print("256 storeAnswer")
    dict = json.loads(postIDAndAnswer)
    username = dict['username']
    postID = dict['postId']
    answer = dict['user_answer']
    newDictionary={'username' : username,'postId' : postID, 'user_answer' : answer}
    print("263", newDictionary)

    postInfo = post_collection.find_one({'_id' : postID})
    #Check if the user submitting the answer is the same as the creator of the question
    #if username == postInfo.get('username'):
        #return
    
    if postID in answerStorage:
        answerStorage[postID] = answerStorage[postID].append(newDictionary)
    else:
        answerStorage[postID] = [newDictionary]
    print("274 answerStorage", answerStorage)

@socketio.on("gradeQuestion")
def gradeQuestion(postID): #postID should be a string
    #Check if an answer is submitted for the question
    print("279 answerStorage", answerStorage)
    if postID not in answerStorage:
        print("postID not in answerStorage")
        return
    
    answer_data = answerStorage[postID] #list
    for answer in answer_data:
        user_answer = answer['user_answer']

        postInfo = post_collection.find_one({'_id' : postID})
        title = postInfo['title']
        description = postInfo['description']
        expectedAnswer = postInfo['answer']
        
        print("291 postID", postID)
        post_collection.delete_one({'_id': postID})

        del answerStorage[postID]
        emit('updateHTML')
        score = 0
        if str(user_answer).isnumeric() != str(expectedAnswer).isnumeric():
            #Not the same answer
            score = 0
        elif str(user_answer).isnumeric() and str(expectedAnswer).isnumeric():
            if int(user_answer) == int(expectedAnswer):
                score = 1
        else:
            if user_answer == expectedAnswer:
                score = 1
        out = {'username' : answer['username'] ,'title' : title, 'description' : description, 'user_answer' : user_answer, 'expected_answer' : expectedAnswer, 'score' : score}
        #print("server.py 294 out", out)
        grade_collection.insert_one(out)
        #Sending this to JS to create HTML for grading of each question
        #emit('create_grade',out)

if __name__ == "__main__":
    #app.run(debug=True, host='0.0.0.0', port=8080)
    socketio.run(app, host= '0.0.0.0' , port= 8080)
