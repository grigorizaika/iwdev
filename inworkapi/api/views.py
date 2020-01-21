import django_filters.rest_framework
import json
import phonenumbers

from api.serializers import (
    AddressSerializer, ClientSerializer, CompanySerializer, UserSerializer, RegistrationSerializer, OrderSerializer, TaskSerializer)
from django_cognito_jwt import JSONWebTokenAuthentication
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import generics
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.helpers import (create_address, create_presigned_post, slice_fields, json_list_group_by)
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from clients.models import Client
from orders.models import (Order, Task)
from users.models import (User as CustomUser, Role, Company)
from utils.models import Address

from tokens_test import get_tokens_test
@api_view(['POST'])
@authentication_classes([])
def get_jwt_tokens(request, **kwargs):
    print(request.data)
    username = request.data.get('username')
    password = request.data.get('password')
    data = {}
    data['username'] = username
    data['password'] = password
    tokens = get_tokens_test(username, password)
    return Response(tokens)

# Function-based views
@api_view(['GET'])
@authentication_classes([BasicAuthentication, JSONWebTokenAuthentication])
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
    print("in check_phone with data ", request.query_params)
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

# Class-based views

class UserView(APIView):
    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]
    #http_method_names = ['get', 'post', 'patch', 'delete']

    
    def get(self, request, **kwargs):

        queryset = CustomUser.objects.all()

        if 'id' in kwargs:
            user_id = kwargs.get('id')
            print("Executing GET request to Users, with id ", user_id)
            user = get_object_or_404(queryset, id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
           serializer = UserSerializer(queryset, many=True)
           short_list = slice_fields(['id', 'email', 'name', 'surname',], serializer.data)
           return Response(short_list)


    def post(self, request, **args):

        data = {}

        processed_data = dict(request.data)

        for key in processed_data:
            processed_data[key] = processed_data[key][0]

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

        processed_data = dict(request.data)

        data = {}

        # Role should not be changed using PATCH request
        if 'role' in processed_data:
            processed_data.pop('role')

        if 'id' in kwargs:
            user_id = kwargs.get('id')

            if processed_data['profile_picture_url']:
                processed_data['profile_picture_url'] = str(processed_data['profile_picture_url'][0])
    
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
    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
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
                data['response'] = 'Address with an id ' + address_id + ' does not exist'
        else:
            queryset = Address.objects.all()
            serializer = AddressSerializer(queryset, many=True)
            data = serializer.data

        return Response(data)

    #def post(self, request, *args,**kwargs):
    #    
    #    serializer = (request.data)

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

    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
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
            short_list = slice_fields(['id', 'name', 'email', 'contact_phone'], serializer.data)
            return Response(short_list)


    def post(self, request, **args):
        print("In ClientView post(), ", request.data)
        serializer = ClientSerializer(data=request.data)
        data = {}

        if serializer.is_valid():
            client = serializer.save()
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

    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
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
        modified_data = dict(request.data)
        modified_data = { key: val[0]  for key, val in modified_data.items() }
        
        if not isinstance(modified_data['client'], int):
            modified_data['client'] = Client.objects.get(name=request.data['client']).id
        
        modified_data['owner'] = Client.objects.get(name=request.data['client']).address_owner.id
        print("Creating new Order: ", modified_data)

        orderSerializer = OrderSerializer(data=modified_data)
        addressSerializer = AddressSerializer(data=modified_data)
        data = {}

        order_valid = orderSerializer.is_valid()
        address_valid = addressSerializer.is_valid()

        if order_valid and address_valid:
            order = orderSerializer.save()
            order.address = addressSerializer.save()
            order.save()
            data['response'] = 'Created order ' + str(order.id) + ' \"' + str(order.name) + '\"'
        else:
            data['orderErrors'] = orderSerializer.errors
            data['addresErrors'] = addressSerializer.errors

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
    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
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

        task_list = json.loads(request.data.get('task_list'))

        print('----------------' + 'Tasks' + '----------------')
        print(task_list)
        print('----------------' + '-----' + '----------------')

        data = {}
        full_response = []

        for task_item in task_list:
            print('-------------' + 'Current task' + '------------')
            print(task_item)
            print('----------------' + '-----' + '----------------')
            taskSerializer = TaskSerializer(data=task_item)
            if taskSerializer.is_valid():
                task = taskSerializer.save()
                full_response.append('Successfully created task ' + str(task.id) + ' ' + task.name ) 
            else:
                full_response.append(str(taskSerializer.errors))
        
        data['response'] = full_response
        
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
@authentication_classes([BasicAuthentication, JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def accept_hours_worked(request, **kwargs):
    task_id = request.data.get('id')
    try:
        task = Task.objects.get(id=task_id)
        task.is_hours_worked_accepted = True
        task.save()
        return Response({ 'response': 'Successfully accepted hours in task ' + task_id })
    except Task.DoesNotExist:
        return Response({ 'response': 'Task id ' + task_id + ' does not exist' })


class CompanyView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]
