# app/tests/test_api.py
# from mock import patch, MagicMock
# from unittest import mock

from app import create_app, mongo
from app.config import TestConfig

from flask_testing import TestCase as FlaskTestCase


###############################################################################
#                         flask test case instance                            #
###############################################################################

class MyTest(FlaskTestCase):

    ############################
    #### setup and teardown ####
    ############################

    def create_app(self):
        app = create_app(TestConfig)
        return app

#    def setUp(self):
        # db.create_all()

 #   def tearDown(self):
        # db.session.remove()
        # db.drop_all()

    ###############################################################################
    #                                tests                                        #
    ###############################################################################

    def test_status_ok(self):
        headers = { 'Content-type': 'application/json' }
        response = self.client.get('/items/status', headers=headers)

        self.assertEqual(response.status_code, 200)

    def reject_non_json(self):
        headers = { 'Content-type': 'text/html' }
        response = self.client.get('/items/status', headers=headers)

        self.assertEqual(response.status_code, 400)

    def test_404(self):
        headers = { 'Content-type': 'application/json' }
        response = self.client.get('/items/non-existent-url', headers=headers)

        self.assertEqual(response.status_code, 404)
