from flask import flash, render_template, url_for, redirect, Blueprint
from __init__ import mongo

############################################################
# MAIN ROUTES
############################################################

main = Blueprint('main', __name__, template_folder="templates")


@main.route('/')
def home():
    """Display the home page."""
    # find all unanswered posts
    post_data = mongo.db.posts.find()

    context = {
        'posts': post_data
    }
    return render_template('home.html', **context)
