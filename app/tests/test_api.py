# app/tests/test_api.py
# from mock import patch, MagicMock
# from unittest import mock
from mock import patch
from functools import wraps
from .fixtures import getPublicID, exceptionFactory
from flask import jsonify
# import uuid

# have to mock the require_access_level decorator here before it
# gets attached to any classes or functions


def mock_dec(access_level, request):
    def actual_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            token = request.headers.get('x-access-token')

            if not token:
                return jsonify({'message': 'Naughty one!'}), 401
            pub_id = getPublicID()
            return f(pub_id, request, *args, **kwargs)

        return decorated
    return actual_decorator


patch('app.decorators.require_access_level', mock_dec).start()

from app import create_app, mongo
from app.config import TestConfig
from flask_testing import TestCase as FlaskTestCase


###############################################################################
#                         flask test case instance                            #
###############################################################################

class MyTest(FlaskTestCase):

    def create_app(self):
        app = create_app(TestConfig)
        print("MMMMEEEEP")
        app.logger.warning("Meep")
        return app

    #def setUp(self):
    #    mongo.db.items.drop()

    #def tearDown(self):
    #    mongo.db.items.drop()

    # --------------------------------------------------------------------------- #
    #                                tests                                        #
    # --------------------------------------------------------------------------- #

    def test_status_ok(self):
        headers = {'Content-type': 'application/json'}
        response = self.client.get('/items/status', headers=headers)
        print("YARP")
        self.app.logger.error("BLAH")
        self.assertEqual(response.status_code, 200)

    def test_reject_non_json(self):
        headers = {'Content-type': 'text/html'}
        response = self.client.get('/items/status', headers=headers)

        self.assertEqual(response.status_code, 400)

    def test_404(self):
        headers = {'Content-type': 'application/json'}
        response = self.client.get('/items/non-existent-url', headers=headers)

        self.assertEqual(response.status_code, 404)

    def test_bad_method_ok(self):
        headers = {'Content-type': 'application/json'}
        response = self.client.delete('/items/status', headers=headers)
        self.assertEqual(response.status_code, 405)
