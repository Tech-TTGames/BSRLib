from flask import render_template, current_app
from application import db
from application.errors import bp

@bp.app_errorhandler(404)
def error404(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def error500(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@bp.app_errorhandler(403)
def error403(error):
    current_app.logger.warning('A user has tried to access a forbidden resource!')
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(418)
def error418(error):
    return render_template('errors/418.html'), 418