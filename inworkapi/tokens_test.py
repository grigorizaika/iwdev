#!../inworkenv/bin/python

import boto3
import pprint
import sys
from inworkapi.settings import COGNITO_APP_CLIENT_ID, COGNITO_USER_POOL_ID

def get_tokens_test(username='gregory.zaika@gmail.com', password='Watermelon1#'):

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')

    response = client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
        'USERNAME': username,
        'PASSWORD': password,
        },
        ClientId=COGNITO_APP_CLIENT_ID,
    )

    return response

def refresh_id_token(refresh_token):

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')

    print('refresh_token', refresh_token)
    
    response = client.initiate_auth(
        AuthFlow='REFRESH_TOKEN_AUTH',
        AuthParameters={
            'REFRESH_TOKEN': refresh_token
        },
        #UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_APP_CLIENT_ID,
    )

    return response

def main():
    if len(sys.argv) > 2:
        print(*sys.argv, sep='\n')
        return get_tokens_test(sys.argv[1], sys.argv[2])
    else:
        return get_tokens_test()

#main()
