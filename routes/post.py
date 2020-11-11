from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from __init__ import mongo

############################################################
# POST ROUTES
############################################################
post = Blueprint('post', __name__, template_folder="templates")


@post.route('/create-post', methods=["GET", "POST"])
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

        return redirect(url_for('post.view_post', post_id=post_id))

    else:
        return render_template('create-post.html')


@post.route('/view-post/<post_id>')
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


@post.route('/posts/<sort>')
def show_posts(sort):

    postOrder = sort
    postlist = mongo.db.posts.find({"answered": "unsolved"})
    dropDownList = {
        "newest": ["Newest First", "newest"],
        "oldest": ["Oldest First", "oldest"],
    }
    currentDropDownChoice = dropDownList[postOrder]
    dropDownList.pop(postOrder)

    if postOrder == "newest":
        postArray = []
        for post in postlist:
            postArray.append(post)
        postArray.reverse()
        postlist = postArray

    if postOrder == "random":
        pass

    if postOrder == "viewed":
        pass

    if postOrder == "oldest":
        pass

    context = {
        "dropList": dropDownList,
        "dropCurrent": currentDropDownChoice,
        "posts": postlist
    }

    return render_template('posts.html', **context)


@post.route('/edit-post/<post_id>', methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    """Display the page to edit a post"""

    post = mongo.db.posts.find_one_or_404({"_id": ObjectId(post_id)})
    user_id = current_user.id
    post_author_id = post["authorId"]

    if not user_id == post_author_id:
        return redirect(url_for("post.view_post", post_id=post_id))

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

        return redirect(url_for("post.view_post", post_id=post_id))
    else:

        context = {
            "post": post
        }

        return render_template('edit-post.html', **context)


@post.route('/delete-post/<post_id>', methods=["POST"])
@login_required
def delete_post(post_id):
    """Delete a post by its id"""

    post = mongo.db.posts.find_one_or_404({"_id": ObjectId(post_id)})
    user_id = current_user.id
    post_author_id = post["authorId"]

    if user_id == post_author_id:

        mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
        mongo.db.comments.delete_many({"post_id": post_id})

        return redirect(url_for("profile.myprofile"))

    else:
        return redirect(url_for("post.view_post", post_id=post_id))
