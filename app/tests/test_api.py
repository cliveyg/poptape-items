# app/tests/test_api.py
# from mock import patch, MagicMock
# from unittest import mock
import uuid

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

# from app import create_app, mongo
from app import create_app, mongo
from app.config import TestConfig
from flask_testing import TestCase as FlaskTestCase


###############################################################################
#                         flask test case instance                            #
###############################################################################

def is_valid_uuid(uuid_to_test, version=4):
    try:
        # check for validity of Uuid
        uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True

class MyTest(FlaskTestCase):

    def create_app(self):
        app = create_app(TestConfig)
        return app

    def setUp(self):
        collections = mongo.db.list_collection_names()
        if 'items' in collections:
            self.app.logger.info("Found 'items' collection")
            mongo.db.items.drop()
            self.app.logger.info("'items' collection dropped")

    def tearDown(self):
        collections = mongo.db.list_collection_names()
        if 'items' in collections:
            self.app.logger.info("Found 'items' collection")
            mongo.db.items.drop()
            self.app.logger.info("'items' collection dropped")

    # --------------------------------------------------------------------------- #
    #                                tests                                        #
    # --------------------------------------------------------------------------- #

    def test_status_ok(self):
        headers = {'Content-type': 'application/json'}
        response = self.client.get('/items/status', headers=headers)
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

    def test_create_item_ok(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'my test item',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-vintage'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 201)
        returned_data = response.json
        self.assertTrue(is_valid_uuid(returned_data.get('item_id')), "Invalid item UUID returned")

        pub_id = getPublicID()
        collection_name = 'z'+pub_id.replace('-','')
        self.assertEqual(returned_data.get('bucket_url'), "https://"+collection_name.lower()+".s3.amazonaws.com/")

    def test_create_item_fail_fields_too_short(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'my te',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'comp'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'name' is a required property")


    def test_create_item_fail_no_token(self):
        headers = {'Content-type': 'application/json'}
        create_json = {'name': 'my test item',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-vintage'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_create_item_fail_no_name(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-vintage'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'name' is a required property")

    def test_create_item_fail_no_description(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'blah blah blah',
                       'category': 'computers-vintage'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'description' is a required property")

    def test_create_item_fail_no_category(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'my test item',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'category' is a required property")
