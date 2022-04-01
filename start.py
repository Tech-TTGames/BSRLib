from application import init_app, db
from application.models import User, Post

app = init_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}