
from urllib import request
from flask import Flask, render_template, make_response, request
from pymongo import MongoClient
import bcrypt
import secrets

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")
db = client["database"]         

# Stores usernames and passwords {'username': username_val, 'password': password_val} 
user_db = db["user_db"]                             

# Stores authentication tokens {'token': token_val, 'username': username_val}
auth_tokens = db["auth_tokens"]                     

@app.route('/') 
def index():
    response = make_response(render_template('index.html'))
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

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
def cookieConunter():
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
        client = MongoClient('mongo',27017)
        db = client.database
        user_db = db.user_db
        
        username = request.form['username']
        password = request.form['password']
        user_data = user_db.find_one({"username": username})
        client.close()
        if user_data:
            hashed_PW = bcrypt.hashpw(password.encode('utf-8'), user_data['salt'])
            if hashed_PW == user_data['password']:
                token = secrets.token_hex(32)
                auth_tokens.insert_one({'token': token, 'username': username})
                response = make_response("Login successful")
                response.set_cookie("auth_token", token, max_age=3600, httponly=True)
                return response
            else:
                raise Exception("Invalid password")
        else:
            raise Exception("Username does not exist")
        
    except Exception as e:
        return str(e), 400

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)

