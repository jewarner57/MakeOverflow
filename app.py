from flask import request, redirect, render_template, url_for, flash
from flask_login import fresh_login_required, login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from __init__ import app, mongo

# import route blueprints
from routes.auth import auth
from routes.main import main
from routes.profile import profile

# register app routes
app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(profile)

############################################################
# ERROR ROUTES
############################################################


@app.errorhandler(404)
def page_not_found(e):
    """display a 404 response page"""
    return render_template('404.html'), 404


@app.errorhandler(401)
def not_authorized(e):
    """send the user to the login screen when they try to access a locked page"""
    flash("Confirm Your Identity to Proceed")
    return redirect(url_for("auth.login"))


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
