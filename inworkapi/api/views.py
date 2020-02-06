import boto3
import django_filters.rest_framework
import json
import phonenumbers

from api.serializers import (
    AddressSerializer, ClientSerializer, CompanySerializer, FileSerializer, UserSerializer, 
    PasswordSerializer, RegistrationSerializer, OrderSerializer, TaskSerializer)
from django_cognito_jwt import JSONWebTokenAuthentication
from django.contrib.auth.hashers import check_password
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import generics
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import (
    action, api_view, authentication_classes, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.helpers import (create_address, bulk_create_tasks, 
                        create_presigned_post, slice_fields, 
                        json_list_group_by)
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from clients.models import Client
from inworkapi.settings import COGNITO_APP_CLIENT_ID
from orders.models import (Order, Task)
from tokens_test import get_tokens_test, refresh_id_token
from users.models import (User as CustomUser, Role, Company)
from utils.models import Address, AddressOwner, CustomFile, FileOwner



@api_view(['POST'])
@authentication_classes([])
def get_jwt_tokens(request, **kwargs):
    print(request.data)
    username = request.data.get('username')
    password = request.data.get('password')
    data = {}
    tokens = get_tokens_test(username, password)

    # Get the user
    id_token = tokens.get('AuthenticationResult').get('IdToken')
    auth = JSONWebTokenAuthentication()
    token_validator = auth.get_token_validator(request)
    jwt_payload = token_validator.validate(id_token)
    user = auth.get_user_model().objects.get_or_create_for_cognito(jwt_payload)
    
    data['auth_response'] = tokens
    data['user'] = UserSerializer(user).data
    
    return Response(data)


@api_view(['POST'])
@authentication_classes([])
def refresh_jwt_tokens(request, **kwargs):
    refresh_token = request.data.get('refresh_token')
    data = {}
    
    if refresh_token:
        auth_response = refresh_id_token(refresh_token)

        # Get the user
        id_token = auth_response.get('AuthenticationResult').get('IdToken')
        auth = JSONWebTokenAuthentication()
        token_validator = auth.get_token_validator(request)
        jwt_payload = token_validator.validate(id_token)
        user = auth.get_user_model().objects.get_or_create_for_cognito(jwt_payload)

        data['auth_response'] = auth_response
        data['user'] = UserSerializer(user).data
    else:
        data['response'] = 'Please specify refresh_token in the request body.'

    return Response(data)


# Function-based views
@api_view(['GET'])
@authentication_classes([JSONWebTokenAuthentication])
def get_presigned_upload_url(request, **kwargs):
    bucket_name = 'inwork-s3-bucket'
    location = request.data.get('to')
    file_name = request.data.get('file_name')
    data = {}
    resource_id = request.data.get('id')

    if not location or not file_name:
        data['response'] = 'Must specify \'to\', \'id\' and \'filename\'  parameters in request body'
        return Response(data)

    if location == 'users':
        if request.user.is_authenticated:
            object_name = location + '/' + request.user.email + '/' + file_name
        else:
            data['response'] = 'Sign in to upload a file'
            return Response(data)
    else:
        # TODO: allow upload to client only if admin is assigned to the client
        if resource_id:
            object_name = location + '/' + resource_id + '/' + file_name
        else:
            data['response'] = 'Must specify ' + location[:-1] + ' id'
            return Response(data)

    data = create_presigned_post(bucket_name, object_name)

    return Response(data)


@api_view(['GET'])
def check_phone(request, **kwargs):
    data = {}

    if not request.query_params.get('phone'):
        data['response'] = "Phone number has not been provided"
        return Response(data)

    phone = '+' + request.query_params.get('phone')[1:]

    try:
        user = CustomUser.objects.get(phone=phone)
        print("found User ", user)
        data['response'] = True
        return Response(data)
    except CustomUser.DoesNotExist:
        print("User does not exist ")
        data['response'] = False
        return Response(data)


@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def client_addresses(request, **kwargs):
    
    data = {}
    if 'id' in kwargs:
        if request.method == 'POST':
            try:
                client = Client.objects.get(id=kwargs.get('id'))
                ao = client.address_owner

                processed_data = { k: v[0] for (k, v) in dict(request.data).items() }

                processed_data['owner'] = ao.id

                serializer = AddressSerializer(data=processed_data)
                if serializer.is_valid():
                    address = serializer.save()
                    data['response'] = "Created Address " + str(address)
                    data['data'] = processed_data
                else:
                    data = serializer.errors
            except Client.DoesNotExist:
                data['response'] = 'Client with an id ' + str(kwargs.get('id')) + ' does not exist'
        elif request.method == 'GET':
            try:
                client = Client.objects.get(id=kwargs.get('id'))
                ao = client.address_owner
                queryset = Address.objects.filter(owner=ao)
                serializer = AddressSerializer(queryset, many=True)
                data['response'] = serializer.data
            except Client.DoesNotExist:
                data['response'] = 'Client with an id ' + str(kwargs.get('id')) + ' does not exist'
    else:
        data['response'] = 'Must specify a client ID'

    return Response(data)


@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def model_files(request, **kwargs):
    print('in model_files; kwargs: ' + str(kwargs))

    data = {}
    possible_model_values = {
        'users': CustomUser, 
        'workers': CustomUser,
        'orders': Order, 
        'tasks' : Task,
    }

    if (not 'model' in kwargs or 
        not 'id' in kwargs):
            data['response'] = 'Wrong url for the file endpoint. \
                Please follow this structure: /api/<string:model>/<int:id>/files/'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
    if not kwargs['model'] in list(possible_model_values.keys()):
        data['response'] = ('\'model\' argument must be one of these values: '
                            + str(list(possible_model_values.keys())))
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    model = possible_model_values[kwargs['model']]
    instance_id = kwargs['id']    
        
    if request.method == 'POST':
        try:
            instance = model.objects.get(id=instance_id)
            fo = instance.file_owner

            processed_data = { k: v[0] for (k, v) in dict(request.data).items() }
            processed_data['owner'] = fo.id

            serializer = FileSerializer(data=processed_data)
            if serializer.is_valid():
                file = serializer.save()
                data['response'] = "Created File " + str(file)
                data['data'] = processed_data
            else:
                data = serializer.errors
        except model.DoesNotExist:
            data['response'] = (
                str(model.__name__) + ' with an id ' + 
                str(instance_id) + ' does not exist'
            )
    elif request.method == 'GET':
        try:
            instance = model.objects.get(id=instance_id)
            fo = instance.file_owner
            queryset = CustomFile.objects.filter(owner=fo)
            serializer = FileSerializer(queryset, many=True)
            data['response'] = serializer.data
        except model.DoesNotExist:
            data['response'] = (
                str(model.__name__) + ' with an id ' + 
                str(instance_id) + ' does not exist'
            )
    else:
        data['response'] = 'Must specify a ' + str(model) + ' ID'

    return Response(data)


@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
def my_files(request, **kwargs):   
    me = request.user
    serializer = FileSerializer(me.files(), many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([JSONWebTokenAuthentication])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def change_password(request, **kwargs):
    data = {}
    
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
            client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')

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
    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')
    resonse = client.forgot_password(
        ClientId=COGNITO_APP_CLIENT_ID,
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

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')
    response = client.confirm_forgot_password(
        ClientId=COGNITO_APP_CLIENT_ID,
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

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')
    response = client.resend_confirmation_code(
        ClientId=COGNITO_APP_CLIENT_ID,
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

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')
    response = client.confirm_sign_up(
        ClientId=COGNITO_APP_CLIENT_ID,
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

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')
    
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

    client = boto3.client('cognito-idp', region_name='eu-central-1', aws_access_key_id = 'AKIAQCUV7DHP2BNSLB6R', aws_secret_access_key = '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')
    print(request.data)

    response = client.verify_user_attribute(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
        Code=request.data['confirmation_code'],
    )

    return Response(response, status=status.HTTP_200_OK)
      

# Class-based views
class UserView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]
    
    def get(self, request, **kwargs):
        queryset = CustomUser.objects.all()

        if 'id' in kwargs:
            user_id = kwargs.get('id')
            user = get_object_or_404(queryset, id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
           serializer = UserSerializer(queryset, many=True)
           #short_list = slice_fields(['id', 'email', 'name', 'surname',], serializer.data)
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
            user_id = kwargs.get('id')

            if 'profile_picture_url' in processed_data:
                processed_data['profile_picture_url'] = str(processed_data['profile_picture_url'])

            if 'email' in processed_data:
                processed_data.pop('email')
                data['details'] = '\'email\' field has not been changed as it as an immutable field'

            djangoUser = CustomUser.objects.get(id=user_id)
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
        print('DELETE User')
        data = {}

        if 'id' in kwargs:
            user_id = kwargs.get('id')

            try:
                djangoUser = CustomUser.objects.get(id=user_id)
                djangoUser.delete()
                data['response'] = 'Successfully deleted ' + djangoUser.email
                return Response(data)
            except CustomUser.DoesNotExist:
                data['response'] = 'User with an id + ' + user_id + ' does not exit'
                return Response(data)


class AddressView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, *args, **kwargs):
        data = {}
        if 'id' in kwargs:
            address_id = kwargs.get('id')
            try:
                address = Address.objects.get(id=address_id)
                serializer = AddressSerializer(address)
                data = serializer.data
            except Address.DoesNotExist:
                data['response'] = 'Address with an id ' + str(address_id) + ' does not exist'
        else:
            queryset = Address.objects.all()
            serializer = AddressSerializer(queryset, many=True)
            data = serializer.data

        return Response(data)

    def post(self, request, *args,**kwargs):
        serializer = AddressSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            address = serializer.save()
            data['response'] = 'Created Address' + str(address)
        else:
            data = serializer.errors

        return Response(data)

    def patch(self, request, **kwargs):
        data = {}
        if 'id' in kwargs:
            address_id = kwargs.get('id')
            
            try:
                address = Address.objects.get(id=address_id)
            except Address.DoesNotExist:
                data['response'] = 'Address with an ID ' + str(address_id) + ' does not exist'
                return Response(data)
                
            serializer = AddressSerializer(address, data=request.data, partial=True)

            if serializer.is_valid():
                address = serializer.save()
                data['response'] = 'Updated address ' + str(address.id)
            else:
                data = serializer.errors

            return Response(data)

    def delete(self, request, *args, **kwargs):
        data = {}
        if 'id' in kwargs:
            try:
                address = Address.objects.get(id=kwargs.get('id'))
                address_str = str(address)
                address.delete()
                data['response'] = 'Successfully deleted address ' + address_str
                return Response(status=status.HTTP_204_NO_CONTENT, data=data)
            except Address.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            data['response'] = 'Must specify an id'
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)


class ClientView(APIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, **kwargs):

        queryset = Client.objects.all()

        if 'id' in kwargs:
            client_id = kwargs.get('id')
            client = get_object_or_404(queryset, id=client_id)
            serializer = ClientSerializer(client)
            return Response(serializer.data)
        else:
            serializer = ClientSerializer(queryset, many=True)
            #short_list = slice_fields(['id', 'name', 'email', 'contact_phone'], serializer.data)
            return Response(serializer.data)


    def post(self, request, **args):
        serializer = ClientSerializer(data=request.data)
        data = {}
        
        if serializer.is_valid():
            client = serializer.save()
            ao = AddressOwner.objects.create()
            client.address_owner = ao
            client.save()
            data['response'] = "Created Client " + str(client.name)
        else:
            data = serializer.errors

        return Response(data)


    def patch(self, request, **kwargs):
        if 'id' in kwargs:
            client_id = kwargs.get('id')
            
            client = Client.objects.get(id=client_id)
            
            serializer = ClientSerializer(client, data=request.data, partial=True)
            
            data = {}

            if serializer.is_valid():
                client = serializer.save()
                data['response'] = 'Updated client ' + client.name
            else:
                data = serializer.errors

            return Response(data)


    def delete(self, request, **kwargs):
        # TODO: also delete addresses
        if 'id' in kwargs:
            client_id = kwargs.get('id')

            data = {}

            try:
                client = Client.objects.get(id=client_id)
                client.delete()
                data['response'] = "Successfully deleted " + client.name
                return Response(data)
            except Client.DoesNotExist:
                data['response'] = 'Client with an id ' + str(client_id) + ' does not exit'
                return Response(data)


class OrderView(APIView):

    queryset = Order.objects.all()
    serializer = OrderSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]


    def get(self, request, **kwargs):
        
        data = {}
        print('in orders')
        if 'id' in kwargs:
            order_id = kwargs.get('id')
            try:
                order = Order.objects.get(id=order_id)
                serializer = OrderSerializer(order)
                return Response(serializer.data)
            except Order.DoesNotExist:
                data['response'] = 'Order with an id ' + str(order_id) + ' does not exist'
                return Response(data)
        else:
            queryset = Order.objects.all()
            serializer = OrderSerializer(queryset, many=True)
#            short_list = slice_fields(['id', 'name', 'client'], serializer.data)
            return Response(serializer.data)


    def post(self, request, **kwargs):
        # TODO: clean this mess with the names that contain the word 'data'
        data = {}

        modified_data = dict(request.data)
        modified_data = { key: val[0]  for key, val in modified_data.items() }  
        
        orderSerializer = OrderSerializer(data=modified_data)

        # Check if an address belongs to a client
        address_id = modified_data.get('address')
        client_id = modified_data.get('client')
        
        client_instance = Client.objects.get(id=client_id)

        if not client_instance.addresses().filter(id=address_id).exists():
            data['response'] = 'Address ' + address_id + ' doesn\'t belong to the client ' + client_id
            return Response(data)

        # Proceed to creation
        if orderSerializer.is_valid():
            order = orderSerializer.save()
            order.save()
            
            if 'task_list' in modified_data:
                task_list = json.loads(request.data.get('task_list'))
                bulk_task_creation_response = bulk_create_tasks(task_list, order.id)
                data['response'] = ['Created order ' + str(order.id) + ' \"' + str(order.name) + '\"']
                data['response'].append(bulk_task_creation_response)
            else:
                data['response'] = 'Created order ' + str(order.id) + ' \"' + str(order.name) + '\"'
            
        else:
            data['orderErrors'] = orderSerializer.errors

        return Response(data)


    def patch(self, request, **kwargs):
        
        data = {}

        if 'id' in kwargs:
            order_id = kwargs.get('id')
            order = Order.objects.get(id=order_id)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            data = {}
            if serializer.is_valid():
                client = serializer.save()
                data['response'] = 'Updated order ' + str(order.id) + ' ' + str(order.name)
            else:
                data = serializer.errors
        else:
            data['response'] = 'Must specify the id'

        return Response(data)

    def delete(self, request, **kwargs):

        if 'id' in kwargs:
            order_id = kwargs.get('id')
            data = {}
            try:
                order = Order.objects.get(id=order_id)
                orderName = order.name
                order.delete()
                data['response'] = 'Successfully deleted order ' + str(order_id) + ' ' + str(orderName)
            except Order.DoesNotExist:
                data['response'] = 'Order with an id ' + str(order_id) + ' does not exist'
        else:
            data['response'] = 'Must specify the id'
        return Response(data)

class TaskView(APIView):
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        
        worker_id = request.GET.get('worker')
        date = request.GET.get('date')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        month = request.GET.get('month')
        year = request.GET.get('year')
        group_by_worker = request.GET.get('group_by_worker')

        data = {}

        if 'id' in kwargs:
            task_id = kwargs.get('id')
            try:
                task = Task.objects.get(id=task_id)
                serializer = TaskSerializer(task)
                return Response(serializer.data)
            except Task.DoesNotExist:
                data['response'] = 'Task with an id ' + str(task_id) + ' does not exist'
                return Response(data)
        elif worker_id:
            # TODO: Check admin permissions properly using DRF permissions
            if request.user.role.name == 'Administrator':
                if date:
                    queryset = Task.objects.filter(worker=worker_id).filter(date=date)
                elif date_start and date_end:
                    queryset = Task.objects \
                                        .filter(worker=worker_id) \
                                        .filter(date__gte=date_start) \
                                        .filter(date__lte=date_end)
                elif month and year:
                    queryset = Task.objects \
                                        .filter(date__year=year) \
                                        .filter(date__month=month) \
                                        .filter(worker=worker_id)
                    serializer = TaskSerializer(queryset, many=True)
                    return Response(serializer.data)
                else:
                    queryset = Task.objects.filter(worker=worker_id)
                    # TODO: add this to the message
                    data['comment'] = 'Date wasn\'t specified, returning all task assigned to the worker ' + worker_id        
                serializer = TaskSerializer(queryset, many=True)
                return Response(serializer.data)
            else:
                data['response'] = 'You must have administrator permissions to perform this action'
                return Response(data)
        elif date or (date_start and date_end) or (year and month):
            # When neither worker nor particular task are specified, default to my tasks
            if date:
                if group_by_worker and request.user.role.name == 'Administrator':
                    # Tasks on a paricular day, grouped by workers
                    queryset = Task.objects.filter(date=date)#.values('worker')
                    #query.group_by = ['worker']
                    #queryset = QuerySet(query=query, model=Task)
                else:
                    queryset = Task.objects.filter(worker=request.user.id).filter(date=date)

            elif date_start and date_end:
                queryset = Task.objects \
                                    .filter(worker=request.user.id) \
                                    .filter(date__gte=date_start) \
                                    .filter(date__lte=date_end)
            elif month and year:
                queryset = Task.objects \
                                    .filter(worker=request.user.id) \
                                    .filter(date__year=year) \
                                    .filter(date__month=month)

            serializer = TaskSerializer(queryset, many=True)
            data = serializer.data
                
            if group_by_worker:
                data = json_list_group_by('worker', data)

            return Response(data)
        else:
            print('3')
            # TODO: Check admin permissions properly using DRF permissions
            if request.user.role.name == 'Administrator':
                queryset = Task.objects.all()
                serializer = TaskSerializer(queryset, many=True)
                return Response(serializer.data)
                #short_list = slice_fields(['id', 'order', 'name', 'worker'], serializer.data)
                #return Response(short_list)
            else:
                data['response'] = 'You must have administrator permissions to perform this action'
                return Response(data)


    def post(self, request, **kwargs):
        data = {}
        task_list = json.loads(request.data.get('task_list'))
        bulk_creation_result = bulk_create_tasks(task_list)
        data['response'] = bulk_creation_result
        return Response(data)


    def patch(self, request, **kwargs):
        
        data = {}
        
        if 'id' in kwargs:
            task_id = kwargs.get('id')
            task = Task.objects.get(id=task_id)
            serializer = TaskSerializer(task, data=request.data, partial=True)
            data = {}
            if serializer.is_valid():
                task = serializer.save()
                data['response'] = 'Updated task ' + str(task.id) + ' ' + str(task.name)
            else:
                data = serializer.errors
        else:
            data['response'] = 'Must specify an id'

        return Response(data)


    def delete(self, request, **kwargs):
        
        data = {}

        if 'id' in kwargs:
            task_id = kwargs.get('id')
            data = {}
            try:
                task = Task.objects.get(id=task_id)
                taskName = task.name
                task.delete()
                data['response'] = 'Successfully deleted task ' + str(task_id) + ' ' + str(taskName)
            except Task.DoesNotExist:
                data['response'] = 'Task with an id ' + str(task_id) + ' does not exist'
        else:
            data['response']= 'Must specify an id'

        return Response(data)


@api_view(['PUT'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def accept_hours_worked(request, **kwargs):
    task_id = request.data.get('id')
    try:
        task = Task.objects.get(id=task_id)
        if not task.is_hours_worked_accepted:
            task.is_hours_worked_accepted = True
            task.save()
            return Response({ 'response': 'Successfully accepted hours in task ' + str(task_id) })
        else:
            return Response({ 'response': 'Hours on task ' + str(task_id) + ' were already accepted by an administrator'})
    except Task.DoesNotExist:
        return Response({ 'response': 'Task id ' + str(task_id) + ' does not exist' })


class CompanyView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]


class FileView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]

    def get(self, request, *args, **kwargs):
        data = {}
        if 'id' in kwargs:
            file_id = kwargs.get('id')
            try:
                file = CustomFile.objects.get(id=file_id)
                serializer = FileSerializer(file)
                data = serializer.data
            except CustomFile.DoesNotExist:
                data['response'] = 'File with an id ' + str(file_id) + ' does not exist'
        else:
            queryset = CustomFile.objects.all()
            serializer = FileSerializer(queryset, many=True)
            data = serializer.data

        return Response(data)

    def post(self, request, *args, **kwargs):
        serializer = FileSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            file = serializer.save()
            data['response'] = 'Created file ' + str(file)
        else:
            data = serializer.errors

        return Response(data)

    def patch(self, request, **kwargs):
        if 'id' in kwargs:
            file_id = kwargs.get('id')
            
            try:
                file = CustomFile.objects.get(id=file_id)
            except CustomFile.DoesNotExist:
                data['response'] = 'File with an ID ' + str(file_id) + ' does not exist'
                return Response(data)
                
            serializer = FileSerializer(file, data=request.data, partial=True)
            
            data = {}

            if serializer.is_valid():
                file = serializer.save()
                data['response'] = 'Updated file ' + str(file.id)
            else:
                data = serializer.errors

            return Response(data)

    def delete(self, request, *args, **kwargs):
        data = {}
        if 'id' in kwargs:
            try:
                file = CustomFile.objects.get(id=kwargs.get('id'))
                file_str = str(file)
                file.delete()
                data['response'] = 'Successfully deleted file ' + file_str
                return Response(status=status.HTTP_204_NO_CONTENT, data=data)
            except CustomFile.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            data['response'] = 'Must specify an id'
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
