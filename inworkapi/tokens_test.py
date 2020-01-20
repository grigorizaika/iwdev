#!../inworkenv/bin/python

import boto3
import pprint
import sys
from inworkapi.settings import COGNITO_APP_CLIENT_ID

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

    pp = pprint.PrettyPrinter(indent=4)
    return response

def main():
    if len(sys.argv) > 2:
        print(*sys.argv, sep='\n')
        return get_tokens_test(sys.argv[1], sys.argv[2])
    else:
        return get_tokens_test()

main()
