# app/decorators.py
from app.services import call_requests
from functools import wraps
import os
from dotenv import load_dotenv
from flask import jsonify
from flask import current_app as appy

load_dotenv()

# -----------------------------------------------------------------------------
# this is separate from the views so we can mock it in tests
# -----------------------------------------------------------------------------

def require_access_level(access_level,request): # pragma: no cover
    def actual_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            token = request.headers.get('x-access-token')

            if not token:
                return jsonify({ 'message': 'Naughty one!'}), 401

            headers = { 'Content-Type': 'application/json', 'x-access-token': token }
            url = os.getenv('CHECK_ACCESS_URL')+str(access_level)
            r = call_requests(url, headers)

            if r.status_code != 200:
                return jsonify({ 'message': 'Ooh you are naughty!'}), 401

            returned_json = r.json()

            if 'public_id' in returned_json:
                pub_id = returned_json['public_id']
                return f(pub_id, request, *args, **kwargs)

            return jsonify({ 'message': 'No public_id returned'}), 401

        return decorated
    return actual_decorator 
