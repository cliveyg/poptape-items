# app/extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_uuid import FlaskUUID
from flask_pymongo import PyMongo
import os

# -----------------------------------------------------------------------------
# set up rate limiting
limiter = Limiter(key_func=get_remote_address,
                  default_limits=["50 per minute", "5 per second"])

# -----------------------------------------------------------------------------
# set up flask uuid regex in url finder
flask_uuid = FlaskUUID()

# -----------------------------------------------------------------------------
# set up pymongo
mongo = PyMongo()
