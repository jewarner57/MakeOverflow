from flask import Flask, request, redirect, render_template, url_for, flash
from flask_login import login_user, logout_user, LoginManager, login_required, current_user
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from user import User
import re


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

        context = {
            "name": name,
            "email": email,
        }

        # check if password matches restrictions
        pattern = re.compile("(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}")
        passMatch = pattern.match(password)

        # check if the email has already been used for an account
        emailExists = mongo.db.users.find_one({"email": email})

        if emailExists:
            flash("Email Is Already Associated with an Account.")
            return render_template('signup.html', **context)
        elif not passMatch:
            flash(
                "Password must be 8 characters long with atleast one uppercase and lowercase letter and one number")
            return render_template('signup.html', **context)
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
    print(current_user.id)
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

    user_id = current_user.id

    user_posts = mongo.db.posts.find({"author": user_id})

    context = {
        "user_posts": user_posts
    }

    return render_template('profile.html', **context)


@app.route('/edit-profile', methods=["GET", "POST"])
@login_required
def edit_profile():
    """Display the page to edit a user's profile"""
    if request.method == 'POST':

        name = request.form.get("name")
        email = request.form.get("email")
        user_id = current_user.id

        # get if email already exists in db
        emailExists = mongo.db.users.find({"email": email})

        # if the email already exists and it isn't the users current email
        if emailExists.count() > 0 and not email == current_user.email:
            flash("Email Already Exists.")
            return render_template('edit-profile.html')
        else:
            mongo.db.users.update_one({
                '_id': ObjectId(user_id)
            },
                {
                '$set': {
                    'name': name,
                    'email': email
                }
            })
            return redirect(url_for("myprofile"))
    else:
        return render_template('edit-profile.html')


@app.route('/delete-profile', methods=["POST"])
@login_required
def delete_profile():
    """Delete the user's profile"""
    user_id = current_user.id

    mongo.db.users.delete_one({"_id": ObjectId(user_id)})

    logout()
    return redirect(url_for("home"))

############################################################
# POST ROUTES
############################################################


@app.route('/create-post', methods=["GET", "POST"])
@login_required
def create_post():
    """Display a create post page"""
    if request.method == 'POST':
        title = request.form.get("title")
        content = request.form.get("content")

        post = {
            "title": title,
            "content": content,
            "author": current_user.id
        }

        new_post = mongo.db.posts.insert_one(post)
        post_id = new_post.inserted_id

        return redirect(url_for('view_post', post_id=post_id))

    else:
        return render_template('create-post.html')


@app.route('/view-post/<post_id>')
@login_required
def view_post(post_id):
    """Display a post by its id"""

    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})

    context = {
        "post": post
    }

    return render_template('view-post.html', **context)


if __name__ == '__main__':
    app.run(debug=True)
