from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .helpers import get_user_by_token
from tokens_test import get_tokens, refresh_id_token
from users.serializers import UserSerializer



@api_view(['POST'])
@authentication_classes([])
def get_jwt_tokens(request, **kwargs):
    data = {}

    if (not 'username' in request.data or
        not 'password' in request.data):
        data['response'] = 'Must specify \'username\', \'password\' in the request body'
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    username = request.data['username']
    password = request.data['password']

    # Get tokens
    tokens_result = get_tokens(username, password)

    if not 'AuthenticationResult' in tokens_result:
        # Means that initiate_auth() has thrown an exception from get_tokens() above,
        # its info returned in tokens_result
        data['auth_response'] = tokens_result
        data['user'] = None
        return Response(data, status=status.HTTP_401_UNAUTHORIZED)

    # Get user by validating token
    id_token = tokens_result['AuthenticationResult'].get('IdToken')
    user = get_user_by_token(request, id_token)
    
    data['auth_response'] = tokens_result
    data['user'] = UserSerializer(user).data
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
def refresh_jwt_tokens(request, **kwargs):
    data = {}

    if not 'refresh_token' in request.data:
        data['response'] = 'Must specify \'refresh_token\' in the request body'
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    refresh_token = request.data['refresh_token']

    auth_response = refresh_id_token(refresh_token)
    
    if auth_response['status'] == 'error':
        return Response(auth_response, status=status.HTTP_404_NOT_FOUND)

    # Get user by validating token

    id_token = auth_response['data']['AuthenticationResult'].get('IdToken')
    user = get_user_by_token(request, id_token)

    data['auth_response'] = auth_response
    data['user'] = UserSerializer(user).data
    return Response(data, status=status.HTTP_200_OK)