from flask import flash, render_template, url_for, redirect, Blueprint

############################################################
# ERROR ROUTES
############################################################

error_routes = Blueprint('error_routes', __name__, template_folder="templates")


@error_routes.errorhandler(404)
def page_not_found(e):
    """display a 404 response page"""
    return render_template('404.html'), 404


@error_routes.errorhandler(401)
def not_authorized(e):
    """send the user to the login screen when they try to access a locked page"""
    flash("Confirm Your Identity to Proceed")
    return redirect(url_for("login"))
