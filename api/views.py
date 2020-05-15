from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from inworkapi.decorators import required_body_params
from inworkapi.utils import JSendResponse, TokenHelper
from users.serializers import UserSerializer


@api_view(['POST'])
@authentication_classes([])
@required_body_params(['username', 'password'])
def get_jwt_tokens(request, **kwargs):
    username = request.data['username']
    password = request.data['password']

    try:
        auth_response = TokenHelper.get_tokens(username, password)
        id_token = auth_response['AuthenticationResult'].get('IdToken')
    except KeyError:
        if auth_response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=auth_response).make_json()
            return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        response = JSendResponse(
            status=JSendResponse.ERROR,
            message=str(e),
        ).make_json()
        return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = TokenHelper.get_user_by_token(request, id_token)
        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'auth_response': auth_response,
                'user': UserSerializer(user).data
            }
        ).make_json()
    except Exception as e:
        response = JSendResponse(
            status=JSendResponse.ERROR,
            message=str(e)
        ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@required_body_params(['refresh_token'])
def refresh_jwt_tokens(request, *args, **kwargs):
    refresh_token = request.data['refresh_token']

    try:
        auth_response = TokenHelper.refresh_id_token(refresh_token)
        id_token = auth_response['AuthenticationResult'].get('IdToken')
    except Exception as e:
        # TODO: Make this a boto3 client exception
        response = JSendResponse(
            status=JSendResponse.ERROR,
            message=str(e)
        ).make_json()
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    try:
        user = TokenHelper.get_user_by_token(request, id_token)
        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'auth_response': auth_response,
                'user': UserSerializer(user).data
            }
        ).make_json()
    except Exception as e:
        # TODO: make the exceptions more specfic
        response = JSendResponse(
            status=JSendResponse.ERROR,
            message=str(e)
        ).make_json()

    return Response(response, status=status.HTTP_200_OK)
