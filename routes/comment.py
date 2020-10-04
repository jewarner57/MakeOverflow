from flask import request, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from __init__ import mongo


############################################################
# COMMENT ROUTES
############################################################
comment = Blueprint('comment', __name__, template_folder="templates")


@comment.route('/comment/<post_id>', methods=["POST"])
@login_required
def add_comment(post_id):
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

    return redirect(url_for('post.view_post', post_id=post_id))


@comment.route('/mark-as-solution/<comment_id>')
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

    return redirect(url_for('post.view_post', post_id=ObjectId(post_id)))
