from flask import Flask, request, redirect, render_template, url_for, flash
from flask_login import login_user, logout_user, LoginManager, login_required
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from user import User


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

# create login manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Loads the current user from the database by id and returns a user object"""
    return User(mongo.db.users.find_one({"_id": ObjectId(user_id)}))

############################################################
# ERROR
############################################################


@app.errorhandler(404)
def page_not_found(e):
    """display a 404 response page"""
    return render_template('404.html'), 404


@app.errorhandler(401)
def not_authorized(e):
    """send the user to the login screen when they try to access a locked page"""
    flash("Please Login to View This Page")
    return redirect(url_for("login"))

############################################################
# AUTH ROUTES
############################################################


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
            "date_created": date_created,
            "is_authenticated": True
        }

        # check if the email has already been used for an account
        emailExists = mongo.db.users.find_one({"email": email})

        if emailExists:
            flash("Email Is Already Associated with an Account.")
            return redirect(url_for('signup'))
        else:
            mongo.db.users.insert_one(new_user)
            return redirect(url_for('login'))
    else:
        return render_template('signup.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    """Display the login page."""

    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        if not request.form.get("remember"):
            remember = False
        else:
            remember = True

        user = mongo.db.users.find_one({"email": email})

        # check if user exists and password matches hash
        if not user or not check_password_hash(user["password"], password):
            flash("The email or password you entered is invalid")
            return redirect(url_for('login'))

        userObj = User(user)

        print(remember)

        login_user(userObj, remember=remember)

        return redirect(url_for('myprofile'))

    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout the user"""
    logout_user()
    return redirect(url_for('home'))


############################################################
# MAIN ROUTES
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


@app.route('/myprofile')
@login_required
def myprofile():
    """Display the user's profile"""
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(debug=True)
