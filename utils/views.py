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
from orders.models import Order, Task
from users.models import User as CustomUser


@api_view(['GET'])
@authentication_classes([JSONWebTokenAuthentication])
def get_presigned_upload_url(request, **kwargs):
    data = {}

    if (not 'to' in request.data or 
        not 'file_name' in request.data):
        data['response'] = 'Must specify \'to\', \'id\' and \'filename\'  parameters in request body'
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    location = request.data['to']
    file_name = request.data['file_name']

    if location == 'users':
        # TODO move to permission_classess
        if request.user.is_authenticated:
            object_name = location + '/' + request.user.email + '/' + file_name
        else:
            data['response'] = 'Sign in to upload a file'
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
    else:
        # TODO: allow upload to client only if admin is assigned to the client
        resource_id = request.data.get('id', None)

        if resource_id:
            object_name = location + '/' + resource_id + '/' + file_name
        else:
            data['response'] = 'Must specify ' + location[:-1] + ' id'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    # MIGRATION TODO
    bucket_name = 'inwork-bucket'
    data['response'] = create_presigned_post(bucket_name, object_name)

    return Response(data, status=status.HTTP_200_OK)



@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def model_files(request, **kwargs):

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


class AddressView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, *args, **kwargs):
        data = {}
        if 'id' in kwargs:
            address_id = kwargs.get('id')
            try:
                address = Address.objects.get(id=address_id)
                if not address.owner.get_owner_instance.company == request.user.company:
                    data['response'] = 'Addresse\'s owner company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)    
                serializer = AddressSerializer(address)
                data = serializer.data
            except Address.DoesNotExist:
                data['response'] = 'Address with an id ' + str(address_id) + ' does not exist'
        else:
            # TODO: Filter addresses by the owner's company
            queryset = Address.objects.filter()
            serializer = AddressSerializer(queryset, many=True)
            data = serializer.data

        return Response(data)

    def post(self, request, *args,**kwargs):
        data = {}

        if 'owner' in request.data:
            ao = AddressOwner.objects.get(id=request.data['owner'])
            owner_instance = ao.get_owner_instance()

            if not owner_instance.company == request.user.company:
                data['response'] = 'Instance\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddressSerializer(data=request.data)
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
                owner_instance = address.owner.get_owner_instance()
                if not owner_instance.company == request.user.company:
                    data['response'] = 'Instance\'s company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)
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

                owner_instance = address.owner.get_owner_instance()
                if not owner_instance.company == request.user.company:
                    data['response'] = 'Instance\'s company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)

                address_str = str(address)
                address.delete()
                data['response'] = 'Successfully deleted address ' + address_str
                return Response(status=status.HTTP_204_NO_CONTENT, data=data)
            except Address.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            data['response'] = 'Must specify an id'
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)


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
