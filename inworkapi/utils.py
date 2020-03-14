import boto3
import json
import sys

from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings


class JSendResponse:
    """
        Reseponse with a structure described in
        https://github.com/omniti-labs/jsend
    """
    SUCCESS = 'success'
    FAIL = 'fail'
    ERROR = 'error'
    statuses = [SUCCESS, FAIL, ERROR]


    def __init__(self, status, data=None, message=None):
        
        if not status in self.statuses:
            raise ValueError('Status must be one of these values: {}'.format(self.statuses))
        
        self._status = status

        if not status == self.ERROR and message:
            raise ValueError('Only a response with a status \'error\' can have \'message\' attribute ')

        self._data = data
        self._message = message


    @property
    def status(self):
        return self._status


    @property
    def data(self):
        return self._data


    @property
    def message(self):
        return self._message


    @data.setter
    def data(self, value):
        self._data = value


    @message.setter
    def message(self, value):
        if self.status == self.ERROR:
            self._message = value
        else:
            raise ValueError('Can only set a mesage on a response with an \'error\' status'
                    .format(self._status))


    def make_json(self):
        response_dict = {}
        response_dict['status'] = self._status
        
        if self.data:
            response_dict['data'] = self.data
        elif self.status == self.FAIL or self.status == self.SUCCESS:
            response_dict['data'] = None
        
        if self.message:
            response_dict['message'] = self._message
        elif self.status == self.ERROR:
            response_dict['message'] = None

        # TODO: sholdn't it be "return json.dumps(response_dict, indent=4)"?
        # that way it is displayed without formatting in Postman
        return response_dict


class TokenHelper:

    @staticmethod
    def get_tokens(username, password):

        client = boto3.client(
            'cognito-idp', 
            region_name=settings.COGNITO_AWS_REGION, 
            aws_access_key_id = settings.AWS_ACCESS_KEY_ID, 
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        )

        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
            'USERNAME': username,
            'PASSWORD': password,
            },
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )

        return response


    @staticmethod
    def refresh_id_token(refresh_token):

        client = boto3.client(
            'cognito-idp', 
            region_name = settings.COGNITO_AWS_REGION, 
            aws_access_key_id = settings.AWS_ACCESS_KEY_ID, 
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        )    

        response = client.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            },
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )

        return response

    @staticmethod
    def get_user_by_token(request, token):

        auth = JSONWebTokenAuthentication()
        jwt_payload = auth.get_token_validator(request).validate(token)
        user = auth.get_user_model().objects.get_or_create_for_cognito(jwt_payload)

        return user