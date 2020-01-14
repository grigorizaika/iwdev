import django_filters.rest_framework
import json
import phonenumbers

from api.serializers import (
    AddressSerializer, ClientSerializer, CompanySerializer, UserSerializer, RegistrationSerializer, OrderSerializer, TaskSerializer)
from django_cognito_jwt import JSONWebTokenAuthentication
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

from api.helpers import (create_address, create_presigned_post, slice_fields)
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)
from clients.models import Client
from orders.models import (Order, Task)
from users.models import (User as CustomUser, Role, Company)
from utils.models import Address


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
        data['response'] = "Found User with phone number " + str(phone)
        data['email'] = user.email
        return Response(data)
    except CustomUser.DoesNotExist:
        print("User does not exist ")
        data['response'] = "User with phone number " + str(phone) + " does not exist."
        return Response(data)

# Class-based views

class UserView(APIView):
    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, **args):
        print("Executing GET request to Users, with data ", request.query_params)

        email = request.query_params.get('email')
        queryset = CustomUser.objects.all()

        if email:
            user = get_object_or_404(queryset, email=email)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
            serializer = UserSerializer(queryset, many=True)
            short_list = slice_fields(['id', 'email', 'name', 'surname',], serializer.data)
            return Response(short_list)


    def post(self, request, **args):
        serializer = RegistrationSerializer(data=request.data)
        data = {}

        if serializer.is_valid():
            user = serializer.save()
            
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


    def patch(self, request, **args):
        # Check if admin or self

        print("in data of UserView, data: ", request.data)
        print("email: ", request.query_params.get('email'))

        processed_data = dict(request.data)

        email = request.query_params.get('email')

        role = processed_data.get('role')
        
        if role:
            role_id = Role.objects.get(name=role[0]).id
            processed_data['role'] = role_id

        djangoUser = CustomUser.objects.get(email=email)
        serializer = UserSerializer(
            djangoUser, data=processed_data, partial=True)
        data = {}

        if serializer.is_valid():

            new_display_name = ''

            if request.data.get('name') and request.data.get('surname'):
                new_display_name = request.data.get(
                    'name') + ' ' + request.data.get('surname')
            elif request.data.get('name') and not request.data.get('surname'):
                new_display_name = request.data.get(
                    'name') + ' ' + djangoUser.surname
            elif not request.data.get('name') and request.data.get('surname'):
                new_display_name = djangoUser.name + \
                    ' ' + request.data.get('surname')
            else:
                new_display_name = djangoUser.name + ' ' + djangoUser.surname

            # if request.data.get('phone'):
            #     firebaseUser = firebase_admin.auth.update_user(
            #         djangoUser.firebaseId,
            #         phone_number=request.data.get('phone'),
            #     )
            # elif request.data.get('name') or request.data.get('surname'):
            #     firebaseUser = firebase_admin.auth.update_user(
            #         djangoUser.firebaseId,
            #         display_name=new_display_name,
            #     )

            djangoUser = serializer.save()
            data['response'] = 'Successfully updated user ' + \
                str(email) + ' ' + str(new_display_name)
        else:
            data = serializer.errors

        return Response(data)


    def delete(self, request, email):
        # TODO: also delete adress
        print("In Users' DELETE, data: ", request.data)
        email = request.data.get('email')

        data = {}

        try:
            djangoUser = CustomUser.objects.get(email=email)
            djangoUser.delete()
            data['response'] = "Successfully deleted " + str(email)
            return Response(data)
        except CustomUser.DoesNotExist:
            data['response'] = "User with an email " + \
                str(email) + " does not exit"
            return Response(data)
        #except Exception as e:
        #    data['response'] = "Unhandled exception " + str(e)
        #    return Response(data)


class AddressView(generics.ListCreateAPIView, mixins.DestroyModelMixin):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['owner', 'street', 'city', 'district', 'country']

    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, addressId):
       return get_object_or_404(Address.objects.all(), id=addressId)

    def delete(self, request, *args, **kwargs):
        object = self.get_object(request.query_params.get('id'))
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT, data={ 'response': "Success"})


class ClientView(APIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]

    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, **args):

        email = request.GET.get('email')
        name = request.GET.get('name')
        queryset = Client.objects.all()

        if email:
            client = get_object_or_404(queryset, email=email)
            serializer = ClientSerializer(client)
            return Response(serializer.data)
        elif name:
            client = get_object_or_404(queryset, name=name)
            serializer = ClientSerializer(client)
            return Response(serializer.data)
        else:
            serializer = ClientSerializer(queryset, many=True)
            short_list = slice_fields(['name', 'email', 'contact_phone'], serializer.data)
            return Response(short_list)


    def post(self, request, **args):
        print("In ClientView post(), ", request.data)
        serializer = ClientSerializer(data=request.data)
        data = {}

        if serializer.is_valid():
            client = serializer.save()
            
            address = create_address(
                client.address_owner,
                request.data.get('street'),
                request.data.get('house_no'),
                request.data.get('city'),
                request.data.get('district'),
                request.data.get('country'),
                request.data.get('flat_no'),
            )

            client.address = address
            client.save()

            data['response'] = "Created Client " + str(client.name)
        else:
            data = serializer.errors

        return Response(data)


    def patch(self, request, **args):

        name = request.query_params.get('name')
        client = Client.objects.get(name=name)
        serializer = ClientSerializer(client, data=request.data, partial=True)
        data = {}

        if serializer.is_valid():
            client = serializer.save()
            data['response'] = 'Updated client ' + name
        else:
            data = serializer.errors

        return Response(data)


    def delete(self, request, name):
        # TODO: also delete adress
        name = request.data.get('name')
        data = {}

        try:
            client = Client.objects.get(name=name)
            client.delete()
            data['response'] = "Successfully deleted " + str(name)
            return Response(data)
        except Client.DoesNotExist:
            data['response'] = "Client with a name " + \
                str(name) + " does not exit"
            return Response(data)
        except Exception as e:
            data['response'] = "Unhandled exception " + e.message


class OrderView(APIView):

    queryset = Order.objects.all()
    serializer = OrderSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']

    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]


    def get(self, request, **args):
        orderId = request.GET.get('id')
        data = {}
        if orderId:
            try:
                order = Order.objects.get(id=orderId)
                serializer = OrderSerializer(order)
                return Response(serializer.data)
            except Order.DoesNotExist:
                data['response'] = 'Order with an id ' + orderId + ' does not exist'
                return Response(data)
        else:
            queryset = Order.objects.all()
            serializer = OrderSerializer(queryset, many=True)
            short_list = slice_fields(['id', 'name', 'client'], serializer.data)
            return Response(short_list)


    def post(self, request, **args):       
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


    def patch(self, request, **args):
        orderId = request.query_params.get('id')
        order = Order.objects.get(id=orderId)
        serializer = OrderSerializer(order, data=request.data, partial=True)
        data = {}
        if serializer.is_valid():
            client = serializer.save()
            data['response'] = 'Updated order ' + str(order.id) + ' ' + str(order.name)
        else:
            data = serializer.errors
        return Response(data)


    def delete(self, request, id):
        orderId = request.data.get('id')
        data = {}
        try:
            order = Order.objects.get(id=orderId)
            orderName = order.name
            order.delete()
            data['response'] = 'Successfully deleted order ' + str(orderId) + ' ' + str(orderName)
        except Order.DoesNotExist:
            data['response'] = 'Order with an id ' + str(orderId) + ' does not exist'
        return Response(data)

class TaskView(APIView):
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']
    authentication_classes = [BasicAuthentication, JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, **args):
        task_id = request.GET.get('id')
        worker_id = request.GET.get('worker')
        date = request.GET.get('date')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')

        data = {}

        if task_id:
            try:
                task = Task.objects.get(id=task_id)
                serializer = TaskSerializer(task)
                return Response(serializer.data)
            except Task.DoesNotExist:
                data['response'] = 'Task with an id ' + taskId + ' does not exist'
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
                else:
                    queryset = Task.objects.filter(worker=worker_id)
                    # TODO: add this to the message
                    data['comment'] = 'Date wasn\'t specified, returning all task assigned to the worker ' + worker_id        
                serializer = TaskSerializer(queryset, many=True)
                return Response(serializer.data)
            else:
                data['response'] = 'You must have administrator permissions to perform this action'
                return Response(data)
        elif date or (date_start and date_end):
            # When neither worker nor particular task are specified, default to my tasks
            if date:
                queryset = Task.objects.filter(worker=request.user.id).filter(date=date)
            elif date_start and date_end:
                queryset = Task.objects \
                                        .filter(worker=request.user.id) \
                                        .filter(date__gte=date_start) \
                                        .filter(date__lte=date_end)
            
            serializer = TaskSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            # TODO: Check admin permissions properly using DRF permissions
            if request.user.role.name == 'Administrator':
                queryset = Task.objects.all()
                serializer = TaskSerializer(queryset, many=True)
                short_list = slice_fields(['id', 'order', 'name', 'worker'], serializer.data)
                return Response(short_list)
            else:
                data['response'] = 'You must have administrator permissions to perform this action'
                return Response(data)


    def post(self, request, **args):

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


    def patch(self, request, **args):
        taskId = request.query_params.get('id')
        task = Task.objects.get(id=taskId)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        data = {}
        if serializer.is_valid():
            task = serializer.save()
            data['response'] = 'Updated task ' + str(task.id) + ' ' + str(task.name)
        else:
            data = serializer.errors
        return Response(data)


    def delete(self, request, id):
        taskId = request.data.get('id')
        data = {}
        try:
            task = Task.objects.get(id=taskId)
            taskName = task.name
            task.delete()
            data['response'] = 'Successfully deleted task ' + str(taskId) + ' ' + str(taskName)
        except Task.DoesNotExist:
            data['response'] = 'Task with an id ' + str(taskId) + ' does not exist'
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