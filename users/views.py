import boto3

from botocore import exceptions as botocore_exceptions
from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, mixins, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User as CustomUser, Role, Company
from .serializers import CompanySerializer, PasswordSerializer, RegistrationSerializer, UserSerializer
from api.helpers import generate_temporary_password
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from utils.serializers import AddressSerializer


@api_view(['GET'])
def check_phone(request, **kwargs):
    data = {}

    if not 'phone' in request.query_params:
        data['response'] = "Phone number has not been provided"
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    phone = '+' + request.query_params['phone'][1:]

    try:
        user = CustomUser.objects.get(phone=phone)
        data['response'] = True
        return Response(data)
    except CustomUser.DoesNotExist:
        data['response'] = False
        return Response(data)

from rest_framework.authentication import get_authorization_header
@api_view(['GET'])
#@authentication_classes([JSONWebTokenAuthentication])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def change_password(request, **kwargs):
    data = {}
    
    # TODO: use decorators
    if (not 'old_password' in request.data
        or not 'new_password' in request.data
        or not 'access_token' in request.data):
        data['response'] = '''Must specify \'old_password\', 
            \'new_password\' and \'access_token\' in the request body'''
        return Response(data, status=status.HTTP_400_BAD_REQUEST)    
    
    user = request.user
    serializer = PasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        if check_password(serializer.data['old_password'], user.password):
            client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)

            # TODO: catch An error occurred (NotAuthorizedException) when calling the ChangePassword operation: Invalid Access Token
            response = client.change_password(
                PreviousPassword=serializer.data['old_password'],
                ProposedPassword=serializer.data['new_password'],
                AccessToken=request.data['access_token']
            )
            user.set_password(serializer.data['new_password'])
            user.save()
            return Response({'response': 'Password set'}, status=status.HTTP_200_OK)
        else:
            data['response'] = 'Old password didn\'t match'
            return Response(data, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def initiate_reset_password(request, **kwargs):
    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)
    resonse = client.forgot_password(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(request.user.email),
    )
    return Response(resonse, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def confirm_reset_password(request, **kwargs):
    data = {}

    if not 'new_password' in request.data or not 'confirmation_code' in request.data:
        data['response'] = 'Must specify \'new_password\' and \'confirmation_code\' in the request body'
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)
    response = client.confirm_forgot_password(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(user.email),
        ConfirmationCode = str(request.data['confirmation_code']),
        Password=str(request.data['new_password']),   
    )

    user.set_password(str(request.data['new_password']))
    user.save()

    data['response'] = response

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def resend_confirmation_code(request, **kwargs):

    if not 'id' in kwargs:
        return Response({'response': 'Specify a user id'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(id=kwargs.get('id'))
    except CustomUser.DoesNotExist:
        return Response({'response': 'User with this id does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)
    response = client.resend_confirmation_code(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(user.email),
    )

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def confirm_sign_up(request, **kwargs):

    if (not 'confirmation_code' in request.data or
        not 'email' in request.data):
        return Response({'response': 'Please provide a \'confirmation_code\' in the request body'}, status=status.HTTP_400_BAD_REQUEST)

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)
    response = client.confirm_sign_up(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=request.data['email'],
        ConfirmationCode=request.data['confirmation_code'],
    )

    return Response(response, status=status.HTTP_200_OK)



@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def initiate_verify_attribute(request, **kwargs):
    data = {}
    if ('access_token' not in request.data or
        'attribute_name' not in request.data):
        data['response'] = '''Must specify \'access_token\', \'attribute_name\', 
        and \'confirmation_code\' in the request body'''
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    available_attribute_names = ['email', 'phone_number']

    if request.data['attribute_name'] not in available_attribute_names:
        data['response'] = '''Invalid value for \'attribute_name\'. Possible values are: ''' + str(available_attribute_names)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)
    
    response = client.get_user_attribute_verification_code(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
    )

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def verify_attribute(request, **kwargs):
    data = {}

    if ('access_token' not in request.data or
        'attribute_name' not in request.data or
        'confirmation_code' not in request.data):
        data['response'] = '''Must specify \'access_token\', \'attribute_name\', 
        and \'confirmation_code\' in the request body'''
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    available_attribute_names = ['email', 'phone_number']
    
    if request.data['attribute_name'] not in available_attribute_names:
        data['response'] = '''Invalid value for \'attribute_name\'. Possible values are: ''' + str(available_attribute_names)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)

    response = client.verify_user_attribute(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
        Code=request.data['confirmation_code'],
    )

    return Response(response, status=status.HTTP_200_OK)


# Admin registration flow
@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def admin_create_cognito_user(request, **kwargs):
    data = {}

    if (not 'email' in request.data or
        not 'phone_number' in request.data or
        not 'name' in request.data or
        not 'surname' in request.data):
        data['response'] = 'Must specify \'email\' and \'phone_number\', \'name\' and \'surname\' fields in the request body.'
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
    
    email = request.data['email']
    phone_number = request.data['phone_number']
    name = request.data['name']
    surname = request.data['surname']
    temporary_password = request.data.get('temporary_password', generate_temporary_password())

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)
    
    # TODO: exception handling and response:
    # - ParamValidationError
    try:
        response = client.admin_create_user(
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
        data['status'] = 'error'
        data['message'] = str(e)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

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
        data['status'] = 'error'
        data['data'] = serializer.errors
        client.admin_delete_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=str(email)
        )
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    data['status'] = 'success'
    data['data'] = {}
    data['data']['response'] = response,
    data['data']['user'] = UserSerializer(user).data, 
    data['data']['temporary_password'] = temporary_password
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([])
def respond_to_new_password_required_challenge(request, **kwargs):
    data = {}
    
    if (not 'new_password' in request.data or
        not 'session' in request.data or
        not 'email' in request.data):
        data['response'] = 'Must specify \'email\', \'new_password\' and \'session\' fields in the request body.'
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
    
    email = request.data['email']
    new_password = request.data['new_password']
    session = request.data['session']

    client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION, aws_access_key_id = settings.AWS_ACCESS_KEY_ID, aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY)

    response = client.respond_to_auth_challenge(
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
    except CustomUser.DoesNotExist:
        data['response'] = 'User does not exist'
        data['user'] = None
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    data['response'] = response
    data['user'] = UserSerializer(user).data

    return Response(data, status=status.HTTP_200_OK)


class UserView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]
    
    def get(self, request, **kwargs):
        queryset = CustomUser.objects.filter(company=request.user.company)

        if 'id' in kwargs:
            user_id = kwargs.get('id')
            user = get_object_or_404(queryset, id=user_id)

            if not user.company == request.user.company:
                data['response'] = 'User\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)                

            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
            queryset.filter(company=request.user.company)
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)


    def post(self, request, **args):
        data = {}

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
                data['response'] = 'Successfully registered a new user.'
                data['email'] = user.email
                data['name'] = user.name
            else:
                data['response'] = 'Successfully registered a new user, but address parameters were invalid.'
                data['detail'] = addressSerializer.errors
        else:
            data = serializer.errors

        return Response(data)


    def patch(self, request, **kwargs):
        # Check if admin or self

        processed_data = { k: v[0] for (k, v) in dict(request.data).items() }
        
        data = {}

        # Role should not be changed using PATCH request
        if 'role' in processed_data:
            processed_data.pop('role')

        if 'id' in kwargs:
            user_id = kwargs['id']

            if 'profile_picture_url' in processed_data:
                processed_data['profile_picture_url'] = str(processed_data['profile_picture_url'])

            if 'email' in processed_data:
                processed_data.pop('email')
                data['details'] = '\'email\' field has not been changed as it as an immutable field'

            djangoUser = CustomUser.objects.get(id=user_id)

            if not djangoUser.company == request.user.company:
                data['response'] = 'User\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)    

            serializer = UserSerializer(djangoUser, data=processed_data, partial=True)

            if serializer.is_valid():
                djangoUser = serializer.save()
                data['response'] = 'Successfully updated user ' + djangoUser.email
            else:
                data = serializer.errors

        else:
            data['response'] = 'User id wasn\'t specified'
            
        return Response(data)


    def delete(self, request, **kwargs):
        # TODO: also delete addresses
        data = {}

        if 'id' in kwargs:
            user_id = kwargs.get('id')

            try:
                djangoUser = CustomUser.objects.get(id=user_id)
            
                if not djangoUser.company == request.user.company:
                    data['response'] = 'User\'s company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)    

                djangoUser.delete()
                data['response'] = 'Successfully deleted ' + djangoUser.email
                return Response(data)
            except CustomUser.DoesNotExist:
                data['response'] = 'User with an id + ' + user_id + ' does not exit'
                return Response(data)


class CompanyView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]
