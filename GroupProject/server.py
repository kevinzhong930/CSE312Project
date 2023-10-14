from flask import Flask, render_template, session, jsonify
from flask_socketio import SocketIO
from flask_pymongo import PyMongo

def create_app():
    app = Flask(__name__) #Create instance of Flask 
    app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
    app.config['SESSION_TYPE'] = 'filesystem'
    socketio = SocketIO(app)
    app.config["MONGO_URI"] = "mongodb://mongo:27017/mydatabase"
    mongo = PyMongo(app)

    @app.after_request
    def noSniff(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.route('/')
    @app.route('/main')
    def main():
        posts = list(mongo.db.posts.find())
        return render_template("index.html", posts=posts)
    
    @app.route('/post-history')
    def post_history():
        posts = list(mongo.db.posts.find())
        for post in posts:
            post['_id'] = str(post['_id'])
        return jsonify(posts)


    def messageReceived(methods=['GET', 'POST']):
        print('message was received!!!')

    @socketio.on('submit_post')
    def handle_submit_post(data):
        username = data.get('username', 'Anonymous')  #Use the username from the data or default to 'Anonymous'
        title = data['title']
        description = data['description']

        #Save to MongoDB
        post_id = mongo.db.posts.insert_one({'username': username, 'title': title, 'description': description}).inserted_id

        data['id'] = str(post_id)
        
        #Send the post to all clients
        socketio.emit('new_post', data, room='broadcast')

    return app, socketio  # Return both app and socketio

app, socketio = create_app()

if __name__ == '__main__':
    host = "0.0.0.0"
    port = 8080
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
    #app.run(host=host, port=port) #Starts the Flask server 