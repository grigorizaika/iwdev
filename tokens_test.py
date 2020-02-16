#!../inworkenv/bin/python

import boto3
import pprint
import sys

from django.conf import settings

def get_tokens(username='gregory.zaika@gmail.com', password='Watermelon1#'):
    data = {}
    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)

    try:
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
            'USERNAME': username,
            'PASSWORD': password,
            },
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )
    except Exception as e:
        data['response'] = str(e)
        data['IdToken'] = None
        return data

    return response

def refresh_id_token(refresh_token):
    response = {}

    client = boto3.client('cognito-idp', region_name = settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)    
    
    try:
        response['data'] = client.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            },
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )
        response['status'] = 'success'
    except client.exceptions.UserNotFoundException as e:
        response['status'] = 'error'
        response['message'] = str(e)

    return response

def main():
    if len(sys.argv) > 2:
        print(*sys.argv, sep='\n')
        return get_tokens(sys.argv[1], sys.argv[2])
    else:
        return get_tokens()

#main()
