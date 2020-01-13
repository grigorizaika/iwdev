
def get_tokens() :
    import boto3
    import pprint

    client = boto3.client('cognito-idp')

    response = client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
        'USERNAME': 'gregory.zaika.gmail.com',
        'PASSWORD': 'Watermelon1#'
        },
        ClientId='8n4apo9vid3rje18eijbk6plh',
    )

    pp = pprint.PrettyPrinter(indent=4)
    return pp.pprint(response)