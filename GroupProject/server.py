from flask import Flask, render_template, request, redirect, url_for, flash, make_response, escape
from flask_pymongo import PyMongo
import bcrypt

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"
app.secret_key = "secret_Key"

mongo = PyMongo(app)

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users

        # HTML injection, escape all HTML characters in the username.
        user_name = escape(request.form['user_Name'])
        password = request.form['password']

        # Check if a user name is already exists
        existing_user = users.find_one({'name': user_name})

        # Check username and password are filled
        if not user_name or not password:
            flash('Username or password cannot be empty')
            return redirect(url_for('register'))
        
        # Notify if the username is already taken
        if existing_user:
            flash('Already exists')
            return redirect(url_for('register'))
        
        hash_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        
        users.insert({'name': user_name, 'password': hash_pass})
        flash('Registration success')
        return redirect(url_for('register'))

    return render_template('register.html')


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




if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)

