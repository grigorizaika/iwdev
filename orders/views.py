import django_filters
import json

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

from .models import Order, Task
from .serializers import OrderSerializer, TaskSerializer
from api.helpers import bulk_create_tasks, json_list_group_by
from api.permissions import (IsPostOrIsAuthenticated, IsAdministrator)



class OrderView(APIView):
    queryset = Order.objects.all()
    serializer = OrderSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, **kwargs):

        data = {}
        if 'id' in kwargs:
            order_id = kwargs.get('id')
            try:
                order = Order.objects.get(id=order_id)

                if not order.client.company == request.user.company:
                    data['response'] = 'Order client\'s company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)

                serializer = OrderSerializer(order)

                return Response(serializer.data)
            except Order.DoesNotExist:
                data['response'] = 'Order with an id ' + str(order_id) + ' does not exist'
                return Response(data)
        else:
            queryset = Order.objects.filter(client__company=request.user.company)
            serializer = OrderSerializer(queryset, many=True)
            return Response(serializer.data)


    def post(self, request, **kwargs):
        # TODO: clean this mess with the names that contain the word 'data'
        data = {}

        modified_data = dict(request.data)
        modified_data = { key: val[0]  for key, val in modified_data.items() }

        orderSerializer = OrderSerializer(data=modified_data)

        # Check if an address belongs to a client
        address_id = modified_data.get('address_id')
        client_id = modified_data.get('client_id')

        client_instance = Client.objects.get(id=client_id)

        if not client_instance.company == request.user.company:
            data['response'] = 'Client\'s company doesn\'t match the company of the request user'
            return Response(data, status=status.HTTP_403_FORBIDDEN)

        if not client_instance.addresses().filter(id=address_id).exists():
            data['response'] = 'Client ' + client_id + ' doesn\'t have an address with an id' + address_id 
            return Response(data)

        # Proceed to creation
        if orderSerializer.is_valid():
            order = orderSerializer.save()
            order.save()

            if 'task_list' in modified_data:
                task_list = json.loads(request.data.get('task_list'))
                bulk_task_creation_response = bulk_create_tasks(task_list, request.user, order.id)
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

            if not order.client.company == request.user.company:
                data['response'] = 'Order client\'s company doesn\'t match the request user\'s company'
                return Response(data, status=status.HTTP_403_FORBIDDEN)

            serializer = OrderSerializer(order, data=request.data, partial=True)
            data = {}
            if serializer.is_valid():
                client = serializer.save()
                data['response'] = 'Updated order ' + str(order.id) + ' ' + str(order.name)
            else:
                data = serializer.errors
        else:
            data['response'] = 'Must specify an id'

        return Response(data)

    def delete(self, request, **kwargs):

        if 'id' in kwargs:
            order_id = kwargs.get('id')
            data = {}
            try:
                order = Order.objects.get(id=order_id)
                
                if not order.client.company == request.user.company:
                    data['response'] = 'Order client\'s company doesn\'t match the request user\'s company'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)
                
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
                task = Task.objects.filter(order__client__company=request.user.company).get(id=task_id)
                serializer = TaskSerializer(task)
                return Response(serializer.data)
            except Task.DoesNotExist:
                data['response'] = 'Task with an id ' + str(task_id) + ' does not exist'
                return Response(data)
        elif worker_id:
            # TODO: Check admin permissions properly using DRF permissions
            if request.user.role.name == 'Administrator':
                if date:
                    queryset = Task.objects.filter(order__client__company=request.user.company).filter(worker=worker_id).filter(date=date)
                elif date_start and date_end:
                    queryset = Task.objects \
                                        .filter(order__client__company=request.user.company) \
                                        .filter(worker=worker_id) \
                                        .filter(date__gte=date_start) \
                                        .filter(date__lte=date_end)
                elif month and year:
                    queryset = Task.objects \
                                        .filter(order__client__company=request.user.company) \
                                        .filter(date__year=year) \
                                        .filter(date__month=month) \
                                        .filter(worker=worker_id)
                    serializer = TaskSerializer(queryset, many=True)
                    return Response(serializer.data)
                else:
                    queryset = Task.objects.filter(order__client__company=request.user.company).filter(worker=worker_id)
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
                    queryset = Task.objects.filter(order__client__company=request.user.company).filter(date=date)#.values('worker')
                    #query.group_by = ['worker']
                    #queryset = QuerySet(query=query, model=Task)
                else:
                    queryset = Task.objects.filter(worker=request.user.id).filter(date=date)

            elif date_start and date_end:
                queryset = Task.objects \
                                    .filter(order__client__company=request.user.company) \
                                    .filter(worker=request.user.id) \
                                    .filter(date__gte=date_start) \
                                    .filter(date__lte=date_end)
            elif month and year:
                queryset = Task.objects \
                                    .filter(order__client__company=request.user.company) \
                                    .filter(worker=request.user.id) \
                                    .filter(date__year=year) \
                                    .filter(date__month=month)

            serializer = TaskSerializer(queryset, many=True)
            data = serializer.data

            if group_by_worker:
                data = json_list_group_by('worker_id', data)

            return Response(data)
        else:
            # TODO: Check admin permissions properly using DRF permissions
            if request.user.role.name == 'Administrator':
                queryset = Task.objects.filter(order__client__company=request.user.company)
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
        bulk_creation_result = bulk_create_tasks(task_list, request.user)
        data['response'] = bulk_creation_result
        return Response(data)


    def patch(self, request, **kwargs):
        data = {}
        if 'id' in kwargs:
            task_id = kwargs.get('id')
            task = Task.objects.get(id=task_id)

            if not task.order.client.company == request.user.company:
                data['response'] = 'Task\'s company doesn\'t match the company of the request user'
                return Response(data, status=status.HTTP_403_FORBIDDEN)

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
                if not task.order.client.company == request.user.company:
                    data['response'] = 'Task\'s company doesn\'t match the company of the request user'
                    return Response(data, status=status.HTTP_403_FORBIDDEN)
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
        if not task.order.client.company == user.request.company:
            return Response({ 'response': 'This task belongs to another company than the request user\'s company' }, status=status.HTTP_403_FORBIDDEN)
        if not task.is_hours_worked_accepted:
            task.is_hours_worked_accepted = True
            task.save()
            return Response({ 'response': 'Successfully accepted hours in task ' + str(task_id) })
        else:
            return Response({ 'response': 'Hours on task ' + str(task_id) + ' were already accepted by an administrator'})
    except Task.DoesNotExist:
        return Response({ 'response': 'Task id ' + str(task_id) + ' does not exist' })