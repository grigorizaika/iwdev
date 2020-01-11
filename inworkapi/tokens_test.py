
def get_tokens() :
    # import base64
    # import boto3
    # from warrant.aws_srp import AWSSRP

    # client = boto3.client('cognito-idp')
    # aws = AWSSRP(
    #     username='c4f5a64a-e628-4463-a141-55a9b5f70a0f',
    #     password='sitn1994',
    #     pool_id='eu-central-1_4W9Ujr278',
    #     client_id='6mipnr7jemniq9ng911uh85aub',
    #     client=client
    #     )
    # tokens = aws.authenticate_user()
    # return tokens
    from warrant import Cognito
    u = Cognito(
        'eu-central-1_4W9Ujr278',
        '6mipnr7jemniq9ng911uh85aub',
        username='grigorizaika@outlook.com'
    )
    return u.authenticate(password='Watermelon1#')