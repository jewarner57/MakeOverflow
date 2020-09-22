from flask import Flask, request, redirect, render_template, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv


############################################################
# SETUP
############################################################

# load env variables
load_dotenv()

app = Flask(__name__)
# configure secret key for app
app.secret_key = os.getenv('SECRET_KEY')
# configure mongodb uri
app.config["MONGO_URI"] = "mongodb://localhost:27017/web_final_database"
mongo = PyMongo(app)

############################################################
# ERROR
############################################################


@app.errorhandler(404)
def page_not_found(e):
    # display a 404 response page
    return render_template('404.html'), 404

############################################################
# ROUTES
############################################################


@app.route('/')
def home():
    """Display the home page."""
    # find all users
    user_data = mongo.db.users.find()

    context = {
        'users': user_data
    }
    return render_template('home.html', **context)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Display the signup page."""
    if request.method == 'POST':

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)
        date_created = datetime.now()

        new_user = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "date_created": date_created
        }

        emailExists = mongo.db.users.find_one({"email": email})
        print(emailExists)

        if emailExists:
            flash("Email Is Already Associated with an Account.")
            return redirect(url_for('signup'))

        mongo.db.users.insert_one(new_user)
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    """Display the login page."""
    if request.method == 'POST':
        return render_template('login.html')
    else:
        return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
