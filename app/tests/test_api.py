# app/tests/test_api.py
# from mock import patch, MagicMock
# from unittest import mock
import uuid

from mock import patch
from functools import wraps
from .fixtures import getPublicID, getSpecificPublicID
from flask import jsonify
import datetime

# have to mock the require_access_level decorator here before it
# gets attached to any classes or functions


def mock_dec(access_level, request):
    def actual_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            token = request.headers.get('x-access-token')

            if not token:
                return jsonify({'message': 'Naughty one!'}), 401
            pub_id = getSpecificPublicID()
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


def create_item(**kwargs):

    datein = datetime.datetime.utcnow()

    data = {'name': 'my test item 1',
            'description': 'blah lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
            'category': 'consoles-vintage:3341',
            'yarp': 'narp',
            'public_id': getPublicID(),
            'created': datein,
            'modified': datein}
    # can override default options here
    for key, value in kwargs.items():
        data[key] = value

    item_id = str(uuid.uuid4())

    try:
        mongo.db.items.insert_one({"_id": item_id, "details": data})
    except Exception as e:
        return e

    return item_id, data


class MyTest(FlaskTestCase):

    def create_app(self):
        app = create_app(TestConfig)
        return app

    def setUp(self):
        collections = mongo.db.list_collection_names()
        self.app.logger.info("setUp")
        if 'items' in collections:
            self.app.logger.info("Found 'items' collection")
            mongo.db.items.drop()
            self.app.logger.info("'items' collection dropped")

    def tearDown(self):
        collections = mongo.db.list_collection_names()
        self.app.logger.info("tearDown")
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
                       'category': 'computers-vintage:89898'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 201)
        returned_data = response.json
        self.assertTrue(is_valid_uuid(returned_data.get('item_id')), "Invalid item UUID returned")

    def test_create_item_ok_extra_fields(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'my test item',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-vintage:90003',
                       'yarp': 'narp'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 201)
        returned_data = response.json
        self.assertTrue(is_valid_uuid(returned_data.get('item_id')), "Invalid item UUID returned")

    def test_fetch_item_ok(self):
        item_id, data = create_item(name="name 1")
        headers = {'Content-type': 'application/json'}
        response = self.client.get('/items/'+item_id, headers=headers)
        self.assertEqual(response.status_code, 200)
        returned_data = response.json
        self.assertEqual(item_id, returned_data.get('item_id'))
        self.assertEqual(data.get('description'), returned_data.get('description'))
        self.assertEqual(data.get('yarp'), returned_data.get('yarp'))
        self.assertEqual(data.get('category'), returned_data.get('category'))

    def test_fetch_item_fail_404(self):
        create_item(name="name 1")
        headers = {'Content-type': 'application/json'}
        not_real_item_id = str(uuid.uuid4())
        response = self.client.get('/items/'+not_real_item_id, headers=headers)
        self.assertEqual(response.status_code, 404)
        returned_data = response.json
        self.assertEqual(returned_data.get('message'), 'Could not find the item ['+not_real_item_id+']')

    def test_bulk_fetch_items_ok(self):

        item1_id, data1 = create_item(name="name 1", category="cars-new:90003")
        item2_id, data2 = create_item(name="name 2", category="bikes:90007")

        create_json = {'item_ids': [item1_id, item2_id]}
        headers = {'Content-type': 'application/json'}

        response = self.client.post('/items/bulk/fetch', headers=headers, json=create_json)

        self.assertEqual(response.status_code, 200)
        returned_data = response.json

        returned_item1 = next((item for item in returned_data.get('items') if item['item_id'] == item1_id), None)
        self.assertNotEqual(returned_item1, None)
        returned_item2 = next((item for item in returned_data.get('items') if item['item_id'] == item2_id), None)
        self.assertNotEqual(returned_item2, None)

        self.assertEqual(returned_item1.get('name'), data1.get('name'))
        self.assertEqual(returned_item2.get('name'), data2.get('name'))
        self.assertEqual(returned_item1.get('category'), data1.get('category'))
        self.assertEqual(returned_item2.get('category'), data2.get('category'))

    def test_bulk_fetch_item_ok_other_404(self):

        item1_id, data1 = create_item(name="name 3", category="cars-new:90003")
        item2_id, data2 = create_item(name="name 4", category="bikes:90007")

        create_json = {'item_ids': [item1_id, str(uuid.uuid4())]}
        headers = {'Content-type': 'application/json'}

        response = self.client.post('/items/bulk/fetch', headers=headers, json=create_json)

        self.assertEqual(response.status_code, 200)
        returned_data = response.json

        self.assertEqual(len(returned_data.get('items')), 1)
        returned_item1 = next((item for item in returned_data.get('items') if item['item_id'] == item1_id), None)
        self.assertNotEqual(returned_item1, None)
        returned_item2 = next((item for item in returned_data.get('items') if item['item_id'] == item2_id), None)
        self.assertEqual(returned_item2, None)

        self.assertEqual(returned_item1.get('name'), data1.get('name'))
        self.assertEqual(returned_item1.get('category'), data1.get('category'))

    def test_fail_bulk_fetch_bad_inputs_1(self):
        create_json = {'item_ids': ["some-blah", str(uuid.uuid4())]}
        headers = {'Content-type': 'application/json'}

        response = self.client.post('/items/bulk/fetch', headers=headers, json=create_json)
        returned_message = response.json
        expected_message = {'error': "'some-blah' is too short", 'message': 'Check ya inputs mate.'}
        self.assertDictEqual(returned_message, expected_message)
        self.assertEqual(response.status_code, 400)

    def test_fail_bulk_fetch_bad_inputs_2(self):
        create_json = {'item_ids': ["bca9ee07-e4c8-49ff-b7ee-c1d697d14c9x", str(uuid.uuid4())]}
        headers = {'Content-type': 'application/json'}

        response = self.client.post('/items/bulk/fetch', headers=headers, json=create_json)
        returned_message = response.json
        expected_message = {'error': "'bca9ee07-e4c8-49ff-b7ee-c1d697d14c9x' does not match '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'",
                            'message': 'Check ya inputs mate.'}
        self.assertDictEqual(returned_message, expected_message)
        self.assertEqual(response.status_code, 400)

    def test_fail_bulk_fetch_bad_inputs_3(self):
        create_json = {'something': "bca9ee07-e4c8-49ff-b7ee-c1d697d14c9x"}
        headers = {'Content-type': 'application/json'}

        response = self.client.post('/items/bulk/fetch', headers=headers, json=create_json)
        returned_message = response.json
        expected_message = {'error': "Additional properties are not allowed ('something' was unexpected)",
                            'message': 'Check ya inputs mate.'}
        self.assertDictEqual(returned_message, expected_message)
        self.assertEqual(response.status_code, 400)

    def test_get_items_by_user_ok(self):
        test_data = []
        for x in range(5):
            if x != 4:
                item_id, data = create_item(name="name " + str(x), public_id=getSpecificPublicID())
            else:
                item_id, data = create_item(name="name " + str(x), public_id=getPublicID())
            test_data.append({"item_id": item_id, "data": data})
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items', headers=headers)
        self.assertEqual(response.status_code, 200)
        returned_data = response.json
        self.assertEqual(len(returned_data.get('items')), 4)

        for item in returned_data.get('items'):
            self.assertEqual(item.get('public_id'), getSpecificPublicID())

    def test_get_items_by_user_pagination_ok(self):
        test_data = []
        for x in range(8):
            item_id, data = create_item(name="name " + str(x), public_id=getSpecificPublicID())
            test_data.append({"item_id": item_id, "data": data})
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items', headers=headers)
        self.assertEqual(response.status_code, 200)
        returned_data = response.json
        self.assertEqual(len(returned_data.get('items')), 5)

        for item in returned_data.get('items'):
            self.assertEqual(item.get('public_id'), getSpecificPublicID())

        self.assertEqual(returned_data.get('next_url'), "/items?limit=5&offset=5&sort=id_asc")

        # call again so to obtain page 2
        response2 = self.client.get('/items?limit=5&offset=5&sort=id_asc', headers=headers)
        self.assertEqual(response2.status_code, 200)
        returned_data2 = response2.json
        self.assertEqual(len(returned_data2.get('items')), 3)

        for item in returned_data2.get('items'):
            self.assertEqual(item.get('public_id'), getSpecificPublicID())

        self.assertEqual(returned_data2.get('prev_url'), "/items?limit=5&offset=0&sort=id_asc")

    def test_get_items_by_user_fail_bad_offset_1(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items?limit=5&offset=WIBBLE&sort=id_asc', headers=headers)
        returned_data = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(returned_data.get('message'), "Problem with your args")

    def test_get_items_by_user_fail_bad_offset_2(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items?limit=5&offset=90909090909&sort=id_asc', headers=headers)
        returned_data = response.json
        self.assertEqual(response.status_code, 404)
        self.assertEqual(returned_data.get('message'), "Nowt ere chap")

    def test_get_items_by_user_fail_bad_offset_3(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items?limit=5&offset=-9&sort=id_asc', headers=headers)
        returned_data = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(returned_data.get('message'), "offset cannot be negative")

    def test_get_items_by_user_return_404(self):
        create_item()
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items', headers=headers)
        returned_data = response.json
        self.assertEqual(response.status_code, 404)
        self.assertEqual(returned_data.get('message'), "Nowt ere chap")

    def test_create_item_fail_name_too_short(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'myte',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-new:4002'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'myte' is too short")

    def test_create_item_fail_category_too_short(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'my test name',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'com'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'com' is too short")

    def test_create_item_fail_no_token(self):
        headers = {'Content-type': 'application/json'}
        create_json = {'name': 'my test item',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-vintage:9900'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_create_item_fail_no_name(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'category': 'computers-vintage:8880'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('error'), "'name' is a required property")

    def test_create_item_fail_no_description(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'blah blah blah',
                       'category': 'computers-vintage:98893'}

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

    def test_create_item_fail_bad_json(self):
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        create_json = {'name': 'my test item',
                       'description': 'lorem ipsum lorem ipsum lorem ipsum lorem ipsum',
                       'bad-json': '\uD800'}

        response = self.client.post('/items', json=create_json, headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('message'), "Check ya inputs mate.")

    def test_get_items_by_category_ok(self):
        test_data = []
        sofa_data = []
        for x in range(1, 7):
            if x % 2 == 0:
                item_id, data = create_item(name="name " + str(x), category="fridges-old:1677")
                test_data.append({"item_id": item_id, "data": data})
            else:
                item_id, data = create_item(name="name " + str(x), category="sofas-new:881")
                test_data.append({"item_id": item_id, "data": data})
                data["item_id"] = item_id
                str_date = data.get('created').strftime('%a, %d %b %Y %H:%M:%S ')
                del data['created']
                data['created'] = str_date
                str_date = data.get('modified').strftime('%a, %d %b %Y %H:%M:%S ')
                del data['modified']
                data['modified'] = str_date
                sofa_data.append(data)

        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/cat/sofas-new:881', headers=headers)
        self.assertEqual(response.status_code, 200)
        returned_data = response.json
        self.assertEqual(len(returned_data.get('items')), 3)
        sorted_returned_items = sorted(returned_data.get('items'), key=lambda d: d['item_id'])
        sorted_sofa_data = sorted(sofa_data, key=lambda d: d['item_id'])

        for item in sorted_returned_items:
            self.assertEqual(item.get('category'), "sofas-new:881")

        for x in range(0, 2):
            # removing dates
            del sorted_returned_items[x]['created']
            del sorted_returned_items[x]['modified']
            del sorted_sofa_data[x]['created']
            del sorted_sofa_data[x]['modified']
            self.assertDictEqual(sorted_returned_items[x], sorted_sofa_data[x])

    def test_get_items_by_category_fail_bad_cat(self):
        create_item(name="fred astairmaster", category="stairlifts:8009")
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/cat/stairlifts:800b', headers=headers)
        self.assertEqual(response.status_code, 400)
        returned_data = response.json
        self.assertEqual(returned_data.get('message'), "Invalid category")

    def test_get_items_by_category_404_no_items_with_cat(self):
        create_item(name="fred astairmaster", category="stairlifts:8009")
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/cat/skateboards:6765', headers=headers)
        self.assertEqual(response.status_code, 404)
        returned_data = response.json
        self.assertEqual(returned_data.get('message'), "Nowt in that category lass")

    def test_edit_item_ok(self):
        item_id, data = create_item(name="name 1", public_id=getSpecificPublicID())

        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/'+item_id, headers=headers)
        self.assertEqual(response.status_code, 200)
        data_to_edit = response.json

        data_to_edit['name'] = "edited name"
        edit_response = self.client.put('/items/'+item_id, json=data_to_edit, headers=headers)
        self.assertEqual(edit_response.status_code, 200)

        response3 = self.client.get('/items/'+item_id, headers=headers)
        self.assertEqual(response3.status_code, 200)
        returned_data = response3.json
        self.assertEqual(returned_data.get('name'), "edited name")

    def test_edit_item_fail_json_schema(self):
        item_id, data = create_item(name="name 1", public_id=getSpecificPublicID())

        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/'+item_id, headers=headers)
        self.assertEqual(response.status_code, 200)
        data_to_edit = response.json
        del data_to_edit['description']
        edit_response = self.client.put('/items/'+item_id, json=data_to_edit, headers=headers)
        self.assertEqual(edit_response.status_code, 400)
        returned_data = edit_response.json
        self.assertEqual(returned_data.get('message'), "Check ya inputs mate.")
        self.assertEqual(returned_data.get('error'), "'description' is a required property")

    def test_edit_item_fail_wrong_id(self):
        item_id, data = create_item(name="name 1", public_id=getPublicID())

        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/'+item_id, headers=headers)
        self.assertEqual(response.status_code, 200)
        data_to_edit = response.json

        data_to_edit['name'] = "edited name"
        edit_response = self.client.put('/items/'+item_id, json=data_to_edit, headers=headers)
        self.assertEqual(edit_response.status_code, 401)

    def test_edit_item_fail_item_id_not_found(self):
        item_id, data = create_item(name="name 1", public_id=getPublicID())

        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.get('/items/'+item_id, headers=headers)
        self.assertEqual(response.status_code, 200)
        data_to_edit = response.json

        data_to_edit['name'] = "edited name"
        edit_response = self.client.put('/items/'+str(uuid.uuid4()), json=data_to_edit, headers=headers)
        self.assertEqual(edit_response.status_code, 404)

    def test_delete_item_ok(self):
        item_id, data = create_item(name="name 1", public_id=getSpecificPublicID())
        headers = {'Content-type': 'application/json', 'x-access-token': 'somefaketoken'}
        response = self.client.delete('/items/'+item_id, headers=headers)
        self.assertEqual(response.status_code, 204)