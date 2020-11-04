import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask import Flask
from flask_mail import Mail
from bson.objectid import ObjectId
from user import User

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

# configure mongodb uri for local testing
# dbhost = os.environ.get(
#     'MONGODB_URI', 'mongodb://localhost:27017/web_final_database') + "?retryWrites=false"

mongopass = os.getenv("MONGODBPASS")
mongouser = os.getenv("MONGODBUSER")

app.config["MONGO_URI"] = f"mongodb+srv://{mongouser}:{mongopass}@cluster0.ovfiw.mongodb.net/makeoverflow?retryWrites=true&w=majority"
# create mongo instance
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
