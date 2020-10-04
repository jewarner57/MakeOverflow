from flask import request, redirect, render_template, url_for, flash, Blueprint
from flask_mail import Message
from flask_login import login_user, logout_user, login_required
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
from user import User
import re
from __init__ import app, mongo, mail

############################################################
# AUTH ROUTES
############################################################
auth = Blueprint('auth', __name__, template_folder="templates")


@auth.route('/signup', methods=["GET", "POST"])
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

            return redirect(url_for('auth.login'))
    else:
        return render_template('signup.html')


@auth.route('/login', methods=["GET", "POST"])
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

        return redirect(url_for('profile.myprofile'))

    else:
        return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """Logout the user"""
    logout_user()
    return redirect(url_for('main.home'))


@auth.route('/confirm-email/<token>')
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


@auth.route('/forgot-password', methods=["GET", "POST"])
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
                "auth.reset_password", token=confirmation_token, _external=True)

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


@auth.route('/reset-password/<token>', methods=["GET", "POST"])
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

            return redirect(url_for("auth.login"))

        else:

            flash("Password must be 8 characters long with atleast one uppercase and lowercase letter and one number")
            return render_template("update-password.html")
    else:
        return render_template("update-password.html")


############################################################
# AUTH HELPER METHODS
############################################################

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


def sendConfirmationEmail(email):
    confirmation_token = generate_confirmation_token(email)

    confirm_email_link = url_for(
        "auth.confirm_email", token=confirmation_token, _external=True)

    msg = Message(subject="Confirm your email for MakeOverflow!",
                  html=f"""<a href='{confirm_email_link}'>
                                    Click Here To Authenticate Your Email!
                                </a>""",
                  sender="teedbearjoe@gmail.com",
                  recipients=[email])
    mail.send(msg)
