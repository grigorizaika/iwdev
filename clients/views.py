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
from utils.models import AddressOwner
from utils.serializers import AddressSerializer



class ClientView(APIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, **kwargs):

        queryset = Client.objects.filter(company=request.user.company)

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
            client.company = request.user.company
            client.save()
            data['response'] = "Created Client " + str(client.name)
        else:
            data = serializer.errors

        return Response(data)


    def patch(self, request, **kwargs):
        if 'id' in kwargs:
            client_id = kwargs.get('id')
            
            client = Client.objects.get(id=client_id)

            if not client.company == request.user.company:
                data['response'] = 'Client\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)
            
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

                if not client.company == request.user.company:
                    data['response'] = 'Client\'s company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)

                client.delete()
                data['response'] = "Successfully deleted " + client.name
                return Response(data)
            except Client.DoesNotExist:
                data['response'] = 'Client with an id ' + str(client_id) + ' does not exit'
                return Response(data)



@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def client_addresses(request, **kwargs):
    data = {}

    if not 'id' in kwargs:
        data['response'] = 'Must specify an \'id\' in URL path'
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        try:
            client = Client.objects.get(id=kwargs.get('id'))
            if not client.company == request.user.company:
                data['response'] = 'Client\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)

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
            if not client.company == request.user.company:
                data['response'] = 'Client\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)                
            
            ao = client.address_owner
            queryset = Address.objects.filter(owner=ao)
            serializer = AddressSerializer(queryset, many=True)
            if len(serializer.data) == 0:
                data['response'] = None
            else:
                data['response'] = serializer.data
        except Client.DoesNotExist:
            data['response'] = 'Client with an id ' + str(kwargs.get('id')) + ' does not exist'

    return Response(data)