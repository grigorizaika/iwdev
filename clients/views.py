import django_filters

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

from .models import Client
from .serializers import ClientSerializer
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from inworkapi.utils import JSendResponse
from utils.models import AddressOwner
from utils.serializers import AddressSerializer



class ClientView(APIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, *args, **kwargs):

        queryset = Client.objects.filter(company=request.user.company)

        if 'id' in kwargs:
            # ID specified - return one client with this ID
            client_id = kwargs.get('id')

            try:
                client = queryset.get(id=client_id)
                serializer = ClientSerializer(client)

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data=serializer.data
                ).make_json()
                
                return Response(response, status=status.HTTP_200_OK)

            except Client.DoesNotExist as e:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()
                
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            
        elif not 'id' in kwargs:
            # ID not specified - return client list
            serializer = ClientSerializer(queryset, many=True)

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()
            
            return Response(response, status=status.HTTP_200_OK)


    def post(self, request, *args, **kwargs):
        serializer = ClientSerializer(data=request.data)
        data = {}
        
        if serializer.is_valid():
            client = serializer.save()
            # TODO: move AddressOwner creation to model signal
            ao = AddressOwner.objects.create()
            client.address_owner = ao
            client.company = request.user.company
            client.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={ 'client': f'Created Client {client.name}' }
            ).make_json()
            
            return Response(response, status=status.HTTP_201_CREATED)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=serializer.errors
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, *args, **kwargs):
        if 'id' in kwargs:
            client_id = kwargs.get('id')
            
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist as e:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()

                return Response(response, status=status.HTTP_404_NOT_FOUND)

            # TODO: move to a separate method
            if not client.company == request.user.company:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': 'Client\'s company doesn\'t match the request user\'s company',
                    }
                ).make_json()
                return Response(response, status=status.HTTP_403_FORBIDDEN)
            
            serializer = ClientSerializer(client, data=request.data, partial=True)
            
            if serializer.is_valid():
                client = serializer.save()
                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'client': f'Updated client {client.name}',
                    }
                ).make_json()
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=serializer.errors,
                ).make_json()
                return Response(response, status=status.HTTP_400_BAD_REQUEST)



    def delete(self, request, *args, **kwargs):
        # TODO: also delete addresses
        if 'id' in kwargs:
            client_id = kwargs.get('id')

            try:
                client = Client.objects.get(id=client_id)

                # TODO: move to a separate method
                if not client.company == request.user.company:
                    response = JSendResponse(
                        status=JSendResponse.FAIL,
                        data={
                            'response': 'Client\'s company doesn\'t match the request user\'s company',
                        }
                    ).make_json()
                    return Response(response, status=status.HTTP_403_FORBIDDEN)

                client.delete()
                
                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'client': f'Successfully deleted {client.name}',
                    }
                ).make_json()
                
                return Response(response, status=status.HTTP_204_NO_CONTENT)

            except Client.DoesNotExist as e:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()
                
                return Response(response, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def client_addresses(request, *args, **kwargs):

    if not 'id' in kwargs:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'id': 'Must specify an \'id\' in URL path'
            }
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':

        try:
            client = Client.objects.get(id=kwargs.get('id'))
        except Client.DoesNotExist as e:
            response = JSendResponse(
                status = JSendResponse.FAIL,
                data = str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

            # TODO: move to a separate method
            if not client.company == request.user.company:
            
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': 'Client\'s company doesn\'t match the request user\'s company',
                    }
                ).make_json()
            
                return Response(response, status=status.HTTP_403_FORBIDDEN)

            ao = client.address_owner
            
            processed_data = request.data.dict()
            
            processed_data['owner'] = ao.id
            
            serializer = AddressSerializer(data=processed_data)

            if serializer.is_valid():
            
                address = serializer.save()
                
                response = JSendResponse(
                        status=JSendResponse.SUCCESS,
                        data={
                            'response': f'Created Address {address}',
                            'address': processed_data
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
            client = Client.objects.get(id=kwargs.get('id'))

            # TODO: move to a separate method
            if not client.company == request.user.company:
            
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': 'Client\'s company doesn\'t match the request user\'s company',
                    }
                ).make_json()
            
                return Response(response, status=status.HTTP_403_FORBIDDEN)           
            
            ao = client.address_owner

            queryset = Address.objects.filter(owner=ao)
            
            serializer = AddressSerializer(queryset, many=True)
            
            # TODO: move "[] -> null" into serializer
            if len(serializer.data) == 0:
                data['response'] = None
                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'addresses': None,
                    }
                ).make_json()
            else:
                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'addresses': serializer.data,
                    }
                ).make_json()
                return Response(response, status=status.HTTP_200_OK)
        except Client.DoesNotExist as e:
            response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)