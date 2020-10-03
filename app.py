from flask import Flask, request, redirect, render_template, url_for, flash
from flask_mail import Mail, Message
from flask_login import login_user, logout_user, LoginManager, fresh_login_required, login_required, current_user
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
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
# configure app password salt
app.config["SECURITY_PASSWORD_SALT"] = os.getenv('SECURITY_PASSWORD_SALT')
# configure mongodb uri
app.config["MONGO_URI"] = "mongodb://localhost:27017/web_final_database"
mongo = PyMongo(app)

# create login manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    """Loads the current user from the database by id and returns a user object"""
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if user is None:
        return login_manager.anonymous_user

    return User(user)


# configure flask-mail
mail = Mail()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465

# get password for email from .env

app.config['MAIL_USERNAME'] = 'teedbearjoe@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail.init_app(app)

############################################################
# ERROR
############################################################


@ app.errorhandler(404)
def page_not_found(e):
    """display a 404 response page"""
    return render_template('404.html'), 404


@ app.errorhandler(401)
def not_authorized(e):
    """send the user to the login screen when they try to access a locked page"""
    flash("Confirm Your Identity to Proceed")
    return redirect(url_for("login"))

############################################################
# AUTH ROUTES
############################################################


@ app.route('/signup', methods=["GET", "POST"])
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
            "confirmed_email": False
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

            sendConfirmationEmail(email)

            return redirect(url_for('login'))
    else:
        return render_template('signup.html')


def sendConfirmationEmail(email):
    confirmation_token = generate_confirmation_token(email)

    confirm_email_link = url_for(
        "confirm_email", token=confirmation_token, _external=True)

    msg = Message(subject="Confirm your email for MakeOverflow!",
                  html=f"""<a href='{confirm_email_link}'>
                                    Click Here To Authenticate Your Email!
                                </a>""",
                  sender="teedbearjoe@gmail.com",
                  recipients=[email])
    mail.send(msg)


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
            return render_template('login.html')

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


@app.route('/confirm-email/<token>')
def confirm_email(token):
    """Confirms the user's email."""
    email = confirm_token(token)
    user = mongo.db.users.find_one_or_404({"email": email})

    mongo.db.users.update_one({
        "_id": ObjectId(user["_id"])
    },
        {
        '$set': {
            'confirmed_email': True
        }
    })

    context = {
        "email": email
    }

    return render_template("confirm-email.html", **context)


@app.route('/forgot-password', methods=["GET", "POST"])
def forgot_password():
    """Show forgot password screen"""
    if request.method == "POST":

        email = request.form.get("email")
        confirmation_token = generate_confirmation_token(email)

        user = mongo.db.users.find_one({"email": email})

        if not user["confirmed_email"]:
            flash("Cannot Reset Password With Unverified Email Address")
            return render_template("forgot-password.html")

        if user is not None:

            resetLink = url_for(
                "reset_password", token=confirmation_token, _external=True)

            msg = Message(subject="Reset Your Password for MakeOverflow.",
                          html=f"""<a href='{resetLink}'>
                                    Click Here To Reset Your Password
                                </a>""",
                          sender="teedbearjoe@gmail.com",
                          recipients=[email])
            mail.send(msg)

        flash("Reset Password Email Sent")
        return render_template("forgot-password.html")

    else:
        return render_template("forgot-password.html")


@app.route('/reset-password/<token>', methods=["GET", "POST"])
def reset_password(token):
    """Allow the user to update their password if they have a valid token."""
    email = confirm_token(token)
    user = mongo.db.users.find_one_or_404({"email": email})

    if request.method == "POST":

        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        pattern = re.compile("(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}")
        passMatch = pattern.match(password)

        if passMatch:
            mongo.db.users.update_one({
                "_id": ObjectId(user["_id"])
            },
                {
                '$set': {
                    'password': hashed_password
                }
            })

            return redirect(url_for("login"))

        else:

            flash("Password must be 8 characters long with atleast one uppercase and lowercase letter and one number")
            return render_template("update-password.html")
    else:
        return render_template("update-password.html")


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

############################################################
# MAIN ROUTES
############################################################


@app.route('/')
def home():
    """Display the home page."""
    # find all unanswered posts
    post_data = mongo.db.posts.find()

    context = {
        'posts': post_data
    }
    return render_template('home.html', **context)


@app.route('/myprofile')
@login_required
def myprofile():
    """Display the user's profile"""

    user_id = current_user.id

    user_posts = mongo.db.posts.find({"authorId": user_id})

    context = {
        "user_posts": user_posts
    }

    return render_template('profile.html', **context)


@app.route('/edit-profile', methods=["GET", "POST"])
@fresh_login_required
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

            confirmed_email = current_user.confirmed_email
            if not email == current_user.email:
                sendConfirmationEmail(email)
                confirmed_email = False

            mongo.db.users.update_one({
                '_id': ObjectId(user_id)
            },
                {
                '$set': {
                    'name': name,
                    'email': email,
                    'confirmed_email': confirmed_email
                }
            })
            return redirect(url_for("myprofile"))
    else:
        return render_template('edit-profile.html')


@app.route('/delete-profile', methods=["POST"])
@fresh_login_required
def delete_profile():
    """Delete the user's profile"""
    user_id = current_user.id

    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    mongo.db.posts.delete_many({"authorId": user_id})
    mongo.db.comments.delete_many({"author": user_id})

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
        featured_image = request.form.get("featured-image")

        post = {
            "title": title,
            "content": content,
            "featuredImage": featured_image,
            "authorId": current_user.id,
            "authorName": current_user.name,
            "date_created": datetime.now(),
            "answered": "unsolved"
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

    post = mongo.db.posts.find_one_or_404({"_id": ObjectId(post_id)})
    comments = mongo.db.comments.find({"post_id": post_id})

    context = {
        "post": post,
        "comments": comments
    }

    return render_template('view-post.html', **context)


@app.route('/edit-post/<post_id>', methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    """Display the page to edit a post"""

    post = mongo.db.posts.find_one_or_404({"_id": ObjectId(post_id)})
    user_id = current_user.id
    post_author_id = post["authorId"]

    if not user_id == post_author_id:
        return redirect(url_for("view_post", post_id=post_id))

    if request.method == 'POST':

        title = request.form.get("title")
        content = request.form.get("content")
        featuredImage = request.form.get("featured-image")

        mongo.db.posts.update_one({
            '_id': ObjectId(post_id)
        },
            {
            '$set': {
                'title': title,
                'featuredImage': featuredImage,
                'content': content
            }
        })

        return redirect(url_for("view_post", post_id=post_id))
    else:

        context = {
            "post": post
        }

        return render_template('edit-post.html', **context)


@app.route('/delete-post/<post_id>', methods=["POST"])
@login_required
def delete_post(post_id):
    """Delete a post by its id"""

    post = mongo.db.posts.find_one_or_404({"_id": ObjectId(post_id)})
    user_id = current_user.id
    post_author_id = post["authorId"]

    if user_id == post_author_id:

        mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
        mongo.db.comments.delete_many({"post_id": post_id})

        return redirect(url_for("myprofile"))

    else:
        return redirect(url_for("view_post", post_id=post_id))


############################################################
# COMMENT ROUTES
############################################################
@app.route('/comment/<post_id>', methods=["POST"])
@login_required
def comment(post_id):
    """Save the users comment and send them back to the post they commented on"""

    commentText = request.form.get("comment")

    comment = {
        "post_id": post_id,
        "author": current_user.id,
        "author_name": current_user.name,
        "text": commentText,
        "post_date": datetime.now()
    }

    mongo.db.comments.insert_one(comment)

    return redirect(url_for('view_post', post_id=post_id))


@app.route('/mark-as-solution/<comment_id>')
@login_required
def mark_as_solution(comment_id):
    """Mark the selected comment as the answer to the post"""

    comment = mongo.db.comments.find_one_or_404({"_id": ObjectId(comment_id)})

    post = mongo.db.posts.find_one_or_404(
        {"_id": ObjectId(comment["post_id"])})

    post_author_id = post["authorId"]

    post_id = post["_id"]

    if current_user.id == post_author_id:

        mongo.db.posts.update_one({
            '_id': ObjectId(post_id)
        },
            {
            '$set': {
                'answered': comment["_id"]
            }
        })

        return redirect(url_for('view_post', post_id=ObjectId(post_id)))

    else:
        return redirect(url_for('view_post', post_id=ObjectId(post_id)))


if __name__ == '__main__':
    app.run(debug=True)
