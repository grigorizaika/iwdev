from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render
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

from .helpers import create_presigned_post
from .models import Address, CustomFile
from .serializers import AddressSerializer, FileSerializer
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from inworkapi.decorators import required_body_params
from inworkapi.utils import JSendResponse
from orders.models import Order, Task
from users.models import User as CustomUser


@api_view(['GET'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
@required_body_params(['to', 'file_name'])
def get_presigned_upload_url(request, **kwargs):
    
    location = request.data['to']
    file_name = request.data['file_name']

    if location == 'users':
        
        object_name = location + '/' + request.user.email + '/' + file_name

    else:
        # TODO: allow upload to client only if admin is assigned to the client
        if not 'id' in request.data:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': f'Must specify {location[:-1]} id'
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        resource_id = request.data['id']
        object_name = location + '/' + resource_id + '/' + file_name
    
    # MIGRATION TODO
    bucket_name = 'inwork-bucket'

    response = JSendResponse(
        status=JSendResponse.FAIL,
        data={
            'response': create_presigned_post(bucket_name, object_name)
        }
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def model_files(request, **kwargs):

    possible_model_values = {
        'users': CustomUser, 
        'workers': CustomUser,
        'orders': Order, 
        'tasks' : Task,
    }

    if (not 'model' in kwargs or not 'id' in kwargs):
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': 'Proper URL structure: /api/<string:model>/<int:id>/files/'
            }
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    if not kwargs['model'] in list(possible_model_values.keys()):
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f'\'model\' must be one of these values: { list(possible_model_values.keys()) }'
            }
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    
    model = possible_model_values[kwargs['model']]

    instance_id = kwargs['id']    

    if request.method == 'POST':
        try:
            instance = model.objects.get(id=instance_id)

        except model.DoesNotExist:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': f'{model.__name__} with an id {instance_id} does not exist'
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_404_NOT_FOUND)
                
        fo = instance.file_owner
        
        processed_data = { k: v[0] for (k, v) in dict(request.data).items() }
        
        processed_data['owner'] = fo.id
        
        serializer = FileSerializer(data=processed_data)
        
        if serializer.is_valid():
            file = serializer.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Created File {file}',
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=serializer.errors
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            instance = model.objects.get(id=instance_id)
            fo = instance.file_owner
            
            queryset = CustomFile.objects.filter(owner=fo)
            serializer = FileSerializer(queryset, many=True)
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()
            
            return Response(response, status=status.HTTP_200_OK)

        except model.DoesNotExist:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': f'{model.__name__} with an id {instance_id} does not exist'
                }
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
def my_files(request, **kwargs):   
    me = request.user
    serializer = FileSerializer(me.files(), many=True)
    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=serializer.data
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


class AddressView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, *args, **kwargs):

        if not 'id' in kwargs:
            # TODO: Filter addresses by the owner's company
            queryset = Address.objects.filter()
            serializer = AddressSerializer(queryset, many=True)

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data = serializer.data
            ).make_json()
            
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
            
        address_id = kwargs.get('id')

        try:
            address = Address.objects.get(id=address_id)

        except Address.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not address.owner.get_owner_instance.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data = {
                    'response': 'Addresses\' owner company doesn\'t match your company'
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)    

        serializer = AddressSerializer(address)
        
        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data=serializer.data
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)


    def post(self, request, *args,**kwargs):

        if 'owner' in request.data:
            ao = AddressOwner.objects.get(id=request.data['owner'])
            owner_instance = ao.get_owner_instance()

            if not owner_instance.company == request.user.company:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data = {
                        'response': 'Owner\'s company doesn\'t match your company'
                    }
                ).make_json()

                return Response(response, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddressSerializer(data=request.data)

        if serializer.is_valid():
            address = serializer.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Created Address {address}'
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
        
        if not 'id' in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL, 
                data={ 'id': 'Must specify an id' } 
            ).make_json()
            
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        address_id = kwargs.get('id')
        
        try:
            address = Address.objects.get(id=address_id)
            owner_instance = address.owner.get_owner_instance()

        except Address.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            )

            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not owner_instance.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data = {
                    'response': 'Owner\'s company doesn\'t match your company'
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)
                    
        serializer = AddressSerializer(address, data=request.data, partial=True)
        
        if serializer.is_valid():
            address = serializer.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Updated address {address.id}'
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=serializer.errors
            ).make_json()
    
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):

        if not 'id' in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id'
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = Address.objects.get(id=kwargs.get('id'))
            owner_instance = address.owner.get_owner_instance()
        
        except Address.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            )

            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not owner_instance.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data = {
                    'response': 'Owner\'s company doesn\'t match your company'
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)

        address_str = str(address)
        
        address.delete()
        
        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'response': 'Successfully deleted address {address_str}'
            }
        ).make_json()
        
        return Response(response, status=status.HTTP_204_NO_CONTENT)


class FileView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]

    def get(self, request, *args, **kwargs):
        
        if not 'id' in kwargs:
            queryset = CustomFile.objects.all()
            serializer = FileSerializer(queryset, many=True)
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        file_id = kwargs.get('id')

        try:
            file = CustomFile.objects.get(id=file_id)

        except CustomFile.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': str(e)
                }
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)

        serializer = FileSerializer(file)
        
        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data=serializer.data
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = FileSerializer(data=request.data)

        if serializer.is_valid():
            file = serializer.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Created file {file}'
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
        
        if not 'id' in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id'
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        file_id = kwargs.get('id')
            
        try:
            file = CustomFile.objects.get(id=file_id)
        except CustomFile.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': str(e)
                }
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)
            
        serializer = FileSerializer(file, data=request.data, partial=True)
        
        if serializer.is_valid():
            file = serializer.save()
            
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Updated file {file.id}'
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=serializer.errors
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        
        if not 'id' in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id'
                }
            ).make_json()
            
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            file = CustomFile.objects.get(id=kwargs.get('id'))
        except CustomFile.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': str(e)
                }
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        
        file_str = str(file)

        file.delete()
        
        response= JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'response': f'Successfully deleted file {file_str}'
            }
        ).make_json()
        
        return Response(response, status=status.HTTP_204_NO_CONTENT)
        