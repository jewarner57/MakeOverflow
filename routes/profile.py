from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, fresh_login_required, current_user
from bson.objectid import ObjectId
from routes.auth import sendConfirmationEmail
from __init__ import mongo


############################################################
# PROFILE ROUTES
############################################################
profile = Blueprint('profile', __name__, template_folder="templates")


@profile.route('/myprofile')
@login_required
def myprofile():
    """Display the user's profile"""

    user_id = current_user.id

    user_posts = mongo.db.posts.find({"authorId": user_id})

    context = {
        "user_posts": user_posts
    }

    return render_template('profile.html', **context)


@profile.route('/edit-profile', methods=["GET", "POST"])
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
            return redirect(url_for("profile.myprofile"))
    else:
        return render_template('edit-profile.html')


@profile.route('/delete-profile', methods=["POST"])
@fresh_login_required
def delete_profile():
    """Delete the user's profile"""
    user_id = current_user.id

    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    mongo.db.posts.delete_many({"authorId": user_id})
    mongo.db.comments.delete_many({"author": user_id})

    return redirect(url_for('auth.logout'))
