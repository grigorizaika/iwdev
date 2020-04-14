from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from users import models, views
from inworkapi.utils import JSendResponse


class UserTests(APITestCase):

    initial_user = None

    # TODO: Move credentials to a file?
    # NOTE: Candidate for separate base class attribute
    initial_user_data = {
            'email': 'gzaika.testing@gmail.com',
            'name': 'GZ',
            'surname': 'T',
            'phone': '+48586245124',
            'password': 'Watermelon1#',
        }

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def get_cognito_user(self):
        pass

    def test_cognito_user_created_on_create(self):
        pass

    def test_cognito_user_deleted_on_delete(self):
        pass

    def test_get(self):
        pass

    def test_post_and_get(self):
        pass

    def test_post_invalid_password(self):
        pass

    def test_post_and_get(self):
        pass