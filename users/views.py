from botocore import exceptions as botocore_exceptions
from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, mixins, status
from rest_framework.authentication import get_authorization_header
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User as CustomUser, Role, Company
from .serializers import CompanySerializer, PasswordSerializer, RegistrationSerializer, UserSerializer
from api.helpers import generate_temporary_password
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from inworkapi.decorators import required_body_params
from inworkapi.utils import JSendResponse, CognitoHelper
from utils.serializers import AddressSerializer


@api_view(['GET'])
def check_phone(request, **kwargs):
    # TODO: restrict by the number of requests from the same IP

    if not 'phone' in request.query_params:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'phone': 'Phone number has not been provided'
            }
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    phone = '+' + request.query_params['phone'][1:]

    try:
        user = CustomUser.objects.get(phone=phone)
        
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': True
            }
        ).make_json()
        
        return Response(response, status=status.HTTP_200_OK)

    except CustomUser.DoesNotExist:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': False
            }
        ).make_json()
        return Response(response, status=status.HTTP_200_OK)



@api_view(['GET'])
#@authentication_classes([JSONWebTokenAuthentication])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=serializer.data
    ).make_json()
    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['old_password', 'new_password', 'access_token'])
def change_password(request, **kwargs): 
    
    user = request.user

    serializer = PasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        
        if check_password(serializer.data['old_password'], user.password):
            
            client = CognitoHelper.get_client()

            # TODO: catch An error occurred (NotAuthorizedException) when calling 
            # the ChangePassword operation: Invalid Access Token
            cognito_response = client.change_password(
                PreviousPassword=serializer.data['old_password'],
                ProposedPassword=serializer.data['new_password'],
                AccessToken=request.data['access_token']
            )

            user.set_password(serializer.data['new_password'])
            user.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': cognito_response
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:
    
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': 'Old password didn\'t match'
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)
        

    else:
        
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=serializer.errors
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def initiate_reset_password(request, **kwargs):

    client = CognitoHelper.get_client()
    
    cognito_response = client.forgot_password(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(request.user.email),
    )
        
    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['new_password', 'confirmation_code'])
def confirm_reset_password(request, **kwargs):

    user = request.user

    client = CognitoHelper.get_client()

    cognito_response = client.confirm_forgot_password(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(user.email),
        ConfirmationCode = str(request.data['confirmation_code']),
        Password=str(request.data['new_password']),   
    )

    user.set_password(str(request.data['new_password']))
    user.save()

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def resend_confirmation_code(request, **kwargs):
    response = {}

    if not 'id' in kwargs:

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'id': 'Must specify a user id'
            }
        ).make_json()
        
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(id=kwargs.get('id'))    
    except CustomUser.DoesNotExist as e:
        
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=str(e)
        ).make_json()
        
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    if request.user.is_administrator() or request.user.id == kwargs.get('id'):
        client = CognitoHelper.get_client()
        
        cognito_response = client.resend_confirmation_code(
            ClientId=settings.COGNITO_APP_CLIENT_ID,
            Username=str(user.email),
        )

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=cognito_response
        ).make_json()
 
        return Response(response, status=status.HTTP_200_OK)
    
    response = JSendResponse(
        status=JSendResponse.FAIL,
        data={
            'response': 'Must be administrator or self to perform this action'
        }
    ).make_json()

    return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@required_body_params(['confirmation_code', 'email'])
def confirm_sign_up(request, **kwargs):

    client = CognitoHelper.get_client()

    cognito_response = client.confirm_sign_up(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=request.data['email'],
        ConfirmationCode=request.data['confirmation_code'],
    )

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['access_token', 'attribute_name'])
def initiate_verify_attribute(request, **kwargs):

    available_attribute_names = ['email', 'phone_number']

    if request.data['attribute_name'] not in available_attribute_names:

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f'Possible attribute_name values are: {available_attribute_names}'
            }
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    client = CognitoHelper.get_client()
    
    cognito_response = client.get_user_attribute_verification_code(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
    )

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['access_token', 'attribute_name', 'confirmation_code'])
def verify_attribute(request, **kwargs):
    
    available_attribute_names = ['email', 'phone_number']
    
    if request.data['attribute_name'] not in available_attribute_names:

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f'Possible attribute_name values are: {available_attribute_names}'
            }
        ).make_json()
        
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    client = CognitoHelper.get_client()

    cognito_response = client.verify_user_attribute(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
        Code=request.data['confirmation_code'],
    )

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


# Admin registration flow
@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
@required_body_params(['email', 'phone_number', 'name', 'surname'])
def admin_create_cognito_user(request, **kwargs):
    
    email = request.data['email']
    phone_number = request.data['phone_number']
    name = request.data['name']
    surname = request.data['surname']
    temporary_password = request.data.get('temporary_password', generate_temporary_password())

    client = CognitoHelper.get_client()
    
    try:

        cognito_response = client.admin_create_user(
            UserPoolId = settings.COGNITO_USER_POOL_ID,
            Username = str(email),
            UserAttributes = [
                { 'Name': 'email', 'Value': str(email) },
                { 'Name': 'email_verified', 'Value': 'True' },
                { 'Name': 'phone_number', 'Value': str(phone_number) },
            ],
            TemporaryPassword = temporary_password,
            DesiredDeliveryMediums=['EMAIL'],
        )

    except botocore_exceptions.ParamValidationError as e:

        response = JSendResponse(
            status=JSendResponse.ERROR,
            message=str(e)
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)


    sub = [attribute['Value'] for attribute in response['User']['Attributes'] if attribute['Name'] == 'sub'][0]
    
    user_data = {
        'name'      : name,
        'surname'   : surname,
        'phone'     : phone_number,
        'email'     : email,
        'password'  : temporary_password,
        'password2' : temporary_password,
    }

    serializer = RegistrationSerializer(data=user_data, create_cognito_user=False)
    
    if serializer.is_valid():

        user = serializer.save()

        worker_role, created = Role.objects.get_or_create(name='Worker')

        user.role = worker_role
        user.company = request.user.company
        user.supervisor = request.user
        user.cognito_id = sub

        user.save()

    else: 

        client.admin_delete_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=str(email)
        )

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=serializer.errors    
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data={
            'response': cognito_response,
            'user': UserSerializer(user).data, 
            'temporary_password': temporary_password
        }
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@required_body_params(['new_password', 'session', 'email'])
def respond_to_new_password_required_challenge(request, **kwargs):
    
    email = request.data['email']
    new_password = request.data['new_password']
    session = request.data['session']
    
    client = CognitoHelper.get_client()

    cognito_response = client.respond_to_auth_challenge(
        ClientId= settings.COGNITO_APP_CLIENT_ID,
        ChallengeName='NEW_PASSWORD_REQUIRED',
        Session=session,
        ChallengeResponses={
            'USERNAME': str(email),
            'NEW_PASSWORD': new_password
        },
    )

    try:
        user = CustomUser.objects.get(email=email)

        user.set_password(new_password)
        user.save()

    except CustomUser.DoesNotExist as e:

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': str(e),
                'user': None
            }
        ).make_json()
        
        return Response(response, status=status.HTTP_404_NOT_FOUND)


    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data={
            'cognito_response': cognito_response,
            'user': UserSerializer(user).data
        }
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


class UserView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]
    
    def get(self, request, *args, **kwargs):

        queryset = CustomUser.objects.filter(company=request.user.company)

        if not 'id' in kwargs:
            queryset.filter(company=request.user.company)
            
            serializer = UserSerializer(queryset, many=True)
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)
        
        try:
            user = queryset.get(id=kwargs.get('id'))
        
        except CustomUser.DoesNotExist as e:
            
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)
        
        if not user.company == request.user.company:

            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': 'User\'s company doesn\'t match the request user\'s company'
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(user)
        
        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data=serializer.data
        ).make_json()
        
        return Response(response, status=status.HTTP_200_OK)


    def post(self, request, *args, **kwargs):

        processed_data = { k: v[0] for (k, v) in dict(request.data).items() }

        if processed_data.get('role'):
            del processed_data['role']

        serializer = RegistrationSerializer(data=processed_data)

        if serializer.is_valid():

            user = serializer.save()

            worker_role, created = Role.objects.get_or_create(name='Worker')

            user.role = worker_role
            user.company = request.user.company
            
            user.save()

            owner_id = user.address_owner.id

            addressData = {
                'owner':        owner_id,
                'street':       request.data.get('street'),
                'house_no':     request.data.get('house_no'),
                'flat_no':      request.data.get('flat_no'),
                'city':         request.data.get('city'),
                'district':     request.data.get('district'),
                'country':      request.data.get('country'),
                'postal_code':  request.data.get('postal_code'),
            }

            addressSerializer = AddressSerializer(data=addressData)

            if addressSerializer.is_valid():

                address = addressSerializer.save()

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'email': user.email
                    }
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            else:

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'response': 'Successfully registered a new user, but address parameters were invalid.',
                        'detail': addressSerializer.errors
                    }
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)
                
        else:

            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=serializer.errors
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, **kwargs):
        # Check if admin or self

        processed_data = { k: v[0] for (k, v) in dict(request.data).items() }
        
        data = {}

        # Role should not be changed using PATCH request
        if 'role' in processed_data:
            processed_data.pop('role')

        
        if not 'id' in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'User id wasn\'t specified'
                }
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)
 
        if 'profile_picture_url' in processed_data:
            processed_data['profile_picture_url'] = str(processed_data['profile_picture_url'])

        if 'email' in processed_data:
            processed_data.pop('email')
        
        djangoUser = CustomUser.objects.get(id=kwargs['id'])
        
        if not djangoUser.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': 'User\'s company doesn\'t match the request user\'s company'
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_403_FORBIDDEN)    
        
        serializer = UserSerializer(djangoUser, data=processed_data, partial=True)
        
        if serializer.is_valid():
            djangoUser = serializer.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Successfully updated user {djangoUser.email}'
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)
        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=serializer.errors
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)



    def delete(self, request, **kwargs):
        # TODO: also delete addresses
        data = {}

        if not 'id' in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'User id wasn\'t specified'
                }
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        user_id = kwargs.get('id')

        try:
            djangoUser = CustomUser.objects.get(id=user_id)
        
            if not djangoUser.company == request.user.company:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': 'User\'s company doesn\'t match the request user\'s company'
                    }
                ).make_json()
            
                return Response(response, status=status.HTTP_403_FORBIDDEN)
            
            email = djangoUser.email

            djangoUser.delete()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Successfully deleted user',
                    'email':  str(email)
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_204_NO_CONTENT)

        except CustomUser.DoesNotExist as e:

            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)


class CompanyView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # TODO: JSendResponse format
    