from flask import Flask

from app.extensions import limiter, mongo, flask_uuid
from app.config import Config
from app.errors import handle_429_request, handle_wrong_method, handle_not_found

import logging
from logging.handlers import RotatingFileHandler

def create_app(config_class=Config):

    app = Flask(__name__)
    # set app configs
    app.config.from_object(config_class)

    # logging stuff
    formatter = logging.Formatter("[%(asctime)s] [%(pathname)s:%(lineno)d] %(levelname)s - %(message)s")
    handler = RotatingFileHandler(app.config['LOG_FILENAME'], maxBytes=10000000, backupCount=5)
    log_level = app.config['LOG_LEVEL']

    if log_level == 'DEBUG': # pragma: no cover
        app.logger.setLevel(logging.DEBUG) # pragma: no cover
    elif log_level == 'INFO': # pragma: no cover
        app.logger.setLevel(logging.INFO) # pragma: no cover
    elif log_level == 'WARNING': # pragma: no cover
        app.logger.setLevel(logging.WARNING) # pragma: no cover
    elif log_level == 'ERROR': # pragma: no cover
        app.logger.setLevel(logging.ERROR) # pragma: no cover
    else: # pragma: no cover
        app.logger.setLevel(logging.CRITICAL) # pragma: no cover

    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # initial flask extensions
    limiter.init_app(app)
    flask_uuid.init_app(app)
    # mongo.init_app(app, uri=app.config['MONGO_URI'])
    mongo.init_app(app)

    # blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # register custom errors
    app.register_error_handler(429, handle_429_request)
    app.register_error_handler(405, handle_wrong_method)
    app.register_error_handler(404, handle_not_found)

    return app

