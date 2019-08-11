# items.py

from app import create_app, mongo, limiter, flask_uuid

app = create_app()
#
@app.shell_context_processor
def make_shell_context():
    return dict(app=app, mongo=mongo, limiter=limiter, flask_uuid=flask_uuid)
