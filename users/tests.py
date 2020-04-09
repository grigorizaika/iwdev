from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from users import models, views
from inworkapi.utils import JSendResponse

class AbsenceTests(APITestCase):
    # TODO: Move credentials to a file?
    # NOTE: Candidate for separate APITestCase class attribute
    test_user_data = {
            'email': 'gzaika.testing@gmail.com',
            'name': 'GZ',
            'surname': 'T',
            'phone': '+48586245124',
            'password': 'Watermelon1#',
        }


    def get_absences_url(self, url_kwargs=None):
        return reverse('api:users:absence-list', kwargs=url_kwargs)


    def setUp(self):
        user = models.User.objects.create_user(**self.test_user_data)
        user.role =  models.Role.objects.get_or_create(name='Administrator')[0]
        user.save()
    

    def tearDown(self):
        user = models.User.objects.get(email=self.test_user_data['email'])
        user.delete()
    
    
    # NOTE: Candidate for separate APITestCase class method
    def assertJSendSuccess(self, response):
        self.assertEqual(response.data['status'], JSendResponse.SUCCESS)
        self.assertIn('data', response.data)


    # NOTE: Candidate for separate APITestCase class method
    def assertJSendFail(self, response):
        self.assertEqual(response.data['status'], JSendResponse.FAIL)


    # NOTE: Candidate for separate APITestCase class method
    def get_id_token(self):
        token_grant_endpoint = reverse('api:get-tokens')
        
        data = {
            'username': self.test_user_data['email'],
            'password': self.test_user_data['password']
        }
        
        response = self.client.post(token_grant_endpoint, data=data)
        
        return response.data['data']['auth_response']['AuthenticationResult']['IdToken']


    def get_authenticated_client(self):
        client = APIClient()
        id_token = self.get_id_token()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + id_token)
        return client


    def test_get_absences(self):
        absences_url = self.get_absences_url()
        response = self.get_authenticated_client().get(absences_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSendSuccess(response)


    def test_post_and_get_absence(self):
        pass