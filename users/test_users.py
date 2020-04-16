from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

from users import models
from inworkapi.utils import CognitoHelper


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

    user_test_data = {
        'correct': {
            'email': 'gg@zz.gg',
            'password': 'Watermelon1#',
            'password2': 'Watermelon1#',
            'phone': '+48537703990',
            'name': 'gg',
            'surname': 'zz',
        }
    }

    # NOTE: Candidate for separate base class method
    def get_users_url(self, url_kwargs=None):
        return reverse('api:users:users-list', kwargs=url_kwargs)

    # NOTE: Candidate for separate base class method
    def get_id_token(
            self, email=initial_user_data['email'],
            password=initial_user_data['password']):

        token_grant_endpoint = reverse('api:get-tokens')

        data = {
            'username': email,
            'password': password
        }

        response = self.client.post(token_grant_endpoint, data=data)

        return (response.data['data']['auth_response']
                ['AuthenticationResult']['IdToken'])

    # NOTE: Candidate for separate base class method
    def get_authenticated_client(self):
        client = APIClient()
        id_token = self.get_id_token()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + id_token)
        return client

    def setUp(self):
        user = (models.User.objects
                .create_user(**self.initial_user_data))
        user.role = (models.Role.objects
                     .get_or_create(name='Administrator')[0])
        user.save()

        self.initial_user = user

    def tearDown(self):
        self.initial_user.delete()

    def test_get_list(self):
        users_url = self.get_users_url()
        client = self.get_authenticated_client()
        response = client.get(users_url)

        self.assertEqual(
            response.status_code, status.HTTP_200_OK)
        self.assertIn(
            type(response.data['data']),
            [ReturnList, type(None)])

    def test_get_instance(self):
        users_url = self.get_users_url(
            url_kwargs={'id': self.initial_user.id})
        client = self.get_authenticated_client()
        response = client.get(users_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['data'], ReturnDict)

    def test_post_invalid_password(self):
        pass

    def test_post_and_get(self):
        users_url = self.get_users_url()
        client = self.get_authenticated_client()

        post_response = client.post(
            users_url,
            data=self.user_test_data['correct'])

        self.assertEqual(
            post_response.status_code, status.HTTP_200_OK)

        user_id = post_response.data['data']['id']

        get_response = client.get(
            self.get_users_url(url_kwargs={'id': user_id})
        )

        self.assertEqual(
            get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            get_response.data['data']['email'],
            self.user_test_data['correct']['email'])
        CognitoHelper.assertCognitoUserExists(
            self.user_test_data['correct']['email'])

    def test_patch_and_get(self):
        pass

    def test_delete_and_get(self):
        user_url = self.get_users_url(
            url_kwargs={'id': self.initial_user.id})
        client = self.get_authenticated_client()

        delete_response = client.delete(user_url)

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        CognitoHelper.assertCognitoUserDoesntExist(
            self.initial_user.email)

    # def test_address_owner_created_on_create(self):
        # pass

    # def test_address_owner_deleted_on_delete(self):
        # pass

    # def test_file_owner_created_on_create(self):
        # pass

    # def test_file_owner_deleted_on_delete(self):
        # pass

    def test_admin_registration(self):
        admin_registration_endpoint = reverse(
            'api:users:admin-create-user')
        token_grant_endpoint = reverse('api:get-tokens')
        respond_to_new_password_challenge_endpoint = reverse(
            'api:users:respond-to-new-password-challenge')

        client = self.get_authenticated_client()

        user_data = self.user_test_data['correct'].copy()
        user_data['phone_number'] = user_data.pop('phone')
        user_data.pop('password')
        user_data.pop('password2')

        registration_initiation_response = client.post(
            admin_registration_endpoint,
            data=user_data)

        self.assertEqual(
            registration_initiation_response.status_code,
            status.HTTP_200_OK)

        temporary_password = (registration_initiation_response
                              .data['data']['temporary_password'])

        temporary_login_data = {
            'username': user_data['email'],
            'password': temporary_password
        }

        first_login_response = client.post(
            token_grant_endpoint,
            data=temporary_login_data)

        self.assertEqual(
            first_login_response.status_code,
            status.HTTP_200_OK)

        password_change_data = {
            'email': user_data['email'],
            'session': first_login_response.data['data']['Session'],
            'new_password': self.user_test_data['correct']['password']
        }

        temporary_password_change_response = client.post(
            respond_to_new_password_challenge_endpoint,
            data=password_change_data)

        self.assertEqual(
            temporary_password_change_response.status_code,
            status.HTTP_200_OK)
        self.assertIn('data',
                      temporary_password_change_response.data)
        self.assertIn('cognito_response',
                      temporary_password_change_response.data['data'])
        self.assertIn('AuthenticationResult',
                      temporary_password_change_response.data['data']
                      ['cognito_response'])
        self.assertIn('IdToken',
                      temporary_password_change_response.data['data']
                      ['cognito_response']['AuthenticationResult'])


    # def test_role(self):
        # ?
        # pass


# NOTE: when an exception other than
# assertionError is thrown, tearDown doesn't get
# called, which results in: 'An error occurred
# (UsernameExistsException) when calling the
# SignUp operation: An account with the given email
# already exists'. On the next run it will work correctly,
# because the instance.delete() is called upon that
# UsernameExistsException.
