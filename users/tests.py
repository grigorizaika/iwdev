import datetime
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


    test_absence_data = {
        'correct': {
            'date_start': '2018-06-15',
            'date_end': '2018-07-15',
            'user_id': None,
            'paid': 'True',
            'description': 'Roxanne! You don\'t have to put on the red light'
        },
        'invalid_dates': {
            'date_start': '2018-06-15',
            'date_end': '2017-07-15',
            'user_id': None,
            'paid': 'True',
            'description': 'Roxanne! You don\'t have to put on the red light'
        }
    }


    def get_absences_url(self, url_kwargs=None):
        return reverse('api:users:absence-list', kwargs=url_kwargs)


    def setUp(self):
        user = models.User.objects.create_user(**self.test_user_data)
        user.role =  models.Role.objects.get_or_create(name='Administrator')[0]
        user.save()

        self.test_absence_data['correct']['user_id'] = user.id
        self.test_absence_data['invalid_dates']['user_id'] = user.id
    

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
    def get_id_token(self, email=test_user_data['email'], password=test_user_data['password']):
        token_grant_endpoint = reverse('api:get-tokens')
        
        data = {
            'username': email,
            'password': password
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
        client = self.get_authenticated_client()
        response = client.get(absences_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSendSuccess(response)

    # TODO: Move instance creation to separate method   
    def test_post_and_get_absence(self):
        absences_url = self.get_absences_url()
        client = self.get_authenticated_client()
        
        post_response_correct = client.post(absences_url, data=self.test_absence_data['correct'])
        post_response_invalid_dates = client.post(absences_url, data=self.test_absence_data['invalid_dates'])

        self.assertEqual(post_response_correct.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post_response_invalid_dates.status_code, status.HTTP_400_BAD_REQUEST)

        # Get newly created absence
        absence_id = post_response_correct.data['data']['id']
        absence_url = self.get_absences_url(url_kwargs={'id': absence_id})
        get_response = client.get(absence_url)

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            get_response.data['data']['date_start'], 
            self.test_absence_data['correct']['date_start']
        )
        self.assertEqual(
            get_response.data['data']['date_end'], 
            self.test_absence_data['correct']['date_end']
        )
        self.assertEqual(
            get_response.data['data']['user']['email'], 
            self.test_user_data['email']
        )

    # TODO: Move instance creation to separate method
    def test_create_patch_and_get_absence(self):
        absences_url = self.get_absences_url()
        client = self.get_authenticated_client()
        
        post_response = client.post(absences_url, data=self.test_absence_data['correct'])

        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        absence_id = post_response.data['data']['id']
        absence_url = self.get_absences_url(url_kwargs={'id': absence_id})

        invalid_date_end = datetime.datetime.strptime(
            self.test_absence_data['correct']['date_start'], 
            "%Y-%m-%d"
        ).date() - datetime.timedelta(days=10)

        valid_date_end = datetime.datetime.strptime(
            self.test_absence_data['correct']['date_start'], 
            "%Y-%m-%d"
        ).date() + datetime.timedelta(days=10)

        absence_patch_fields = { 'date_end': invalid_date_end }
        
        patch_response_invalid = client.patch(absence_url, data=absence_patch_fields)

        absence_patch_fields['date_end'] = valid_date_end

        patch_response_valid = client.patch(absence_url, data=absence_patch_fields)

        self.assertEqual(patch_response_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(patch_response_valid.status_code, status.HTTP_200_OK)
        
        get_response = client.get(absence_url)

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            get_response.data['data']['date_start'], 
            self.test_absence_data['correct']['date_start']
        )
        self.assertEqual(
            get_response.data['data']['date_end'], 
            valid_date_end.strftime("%Y-%m-%d")
        )

    # TODO: Move instance creation to separate method
    def test_create_delete_and_get_absence(self):
        absences_url = self.get_absences_url()
        client = self.get_authenticated_client()

        post_response = client.post(absences_url, data=self.test_absence_data['correct'])

        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        absence_id = post_response.data['data']['id']
        absence_url = self.get_absences_url(url_kwargs={'id': absence_id})

        delete_response = client.delete(absence_url)

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        get_response = client.get(absence_url)

        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)