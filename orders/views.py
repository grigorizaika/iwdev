import django_filters
import json

from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, Task
from .serializers import OrderSerializer, TaskSerializer
from api.helpers import bulk_create_tasks, json_list_group_by
from api.permissions import IsAdministrator
from clients.models import Client
from inworkapi.decorators import required_kwargs
from inworkapi.utils import JSendResponse


class OrderView(APIView):
    queryset = Order.objects.all()
    serializer = OrderSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, **kwargs):

        if 'id' in kwargs:

            order_id = kwargs.get('id')

            try:
                order = Order.objects.get(id=order_id)

                if not order.client.company == request.user.company:
                    response = JSendResponse(
                        status=JSendResponse.FAIL,
                        data={
                            'response': """Order\'s company doesn\'t match \
                                the request user\'s company""",
                        }
                    ).make_json()
                    return Response(response, status=status.HTTP_403_FORBIDDEN)

                serializer = OrderSerializer(order)

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data=serializer.data
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            except Order.DoesNotExist as e:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()

                return Response(response, status=status.HTTP_404_NOT_FOUND)

        elif 'id' not in kwargs:
            # TODO: permissions

            queryset = Order.objects.filter(
                client__company=request.user.company)

            serializer = OrderSerializer(queryset, many=True)

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):

        modified_data = request.POST.copy()

        orderSerializer = OrderSerializer(data=modified_data)

        # Check if an address belongs to a client
        address_id = modified_data.get('address_id')
        client_id = modified_data.get('client_id')

        try:
            client_instance = Client.objects.get(id=client_id)
        except Client.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not client_instance.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': """Order\'s company doesn\'t match \
                        the request user\'s company""",
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        if not client_instance.addresses().filter(id=address_id).exists():
            response = JSendResponse(
                status=JSendResponse.ERROR,
                message=f"""Client {client_id} doesn\'t have an address \
                    with an id {address_id}"""
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if orderSerializer.is_valid():
            order = orderSerializer.save()
            order.save()

            if 'task_list' in modified_data:
                # TODO: rewrite it

                task_list = json.loads(request.data.get('task_list'))

                bulk_task_creation_response = bulk_create_tasks(
                    task_list, request.user, order.id)

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'order': str(order),
                        'tasks': bulk_task_creation_response,
                    }
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            else:

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'order': str(order),
                    }
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'order': orderSerializer.errors
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, **kwargs):

        if 'id' not in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id in URL',
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        order_id = kwargs.get('id')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status.HTTP_404_NOT_FOUND)

        if not order.client.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': """Order\'s company doesn\'t \
                        match the request user\'s company""",
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderSerializer(order, data=request.data, partial=True)

        if serializer.is_valid():

            order = serializer.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'order': f'Updated order {order}'
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:

            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'order': serializer.errors
                }
            ).make_json()

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):

        if 'id' not in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id in URL',
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        order_id = kwargs.get('id')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not order.client.company == request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': """Order\'s company doesn\'t match \
                                    the request user\'s company""",
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        orderName = order.name
        order.delete()

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'order': f'Successfully deleted order {order_id} {orderName}',
            }
        ).make_json()

        return Response(response, status=status.HTTP_204_NO_CONTENT)


class TaskView(APIView):
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['client', 'name']
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # TODO: refactor
    def get(self, request, **kwargs):
        worker_id = request.GET.get('worker')
        # TODO: CHenge this variable's name to starts_at
        date = request.GET.get('starts_at')
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        month = request.GET.get('month')
        year = request.GET.get('year')
        group_by_worker = request.GET.get('group_by_worker')

        data = {}

        if 'id' in kwargs:
            task_id = kwargs.get('id')
            try:
                task = (Task.objects
                        .filter(
                            order__client__company=request.user.company)
                        .get(id=task_id))
                serializer = TaskSerializer(task)

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data=serializer.data
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            except Task.DoesNotExist as e:

                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()

                return Response(response, status=status.HTTP_404_NOT_FOUND)

        elif worker_id:
            # TODO: Check admin permissions properly using DRF permissions
            if request.user.role.name == 'Administrator':
                if date:
                    queryset = (Task.objects
                                .filter(
                                    order__client__company=request.user.company)
                                .filter(worker=worker_id)
                                .filter(starts_at=date))
                elif date_start and date_end:
                    queryset = (Task.objects
                                .filter(
                                    order__client__company=request.user.company)
                                .filter(worker=worker_id)
                                .filter(starts_at__gte=date_start)
                                .filter(starts_at__lte=date_end))
                elif month and year:
                    queryset = (Task.objects
                                .filter(
                                    order__client__company=request.user.company)
                                .filter(starts_at__year=year)
                                .filter(starts_at__month=month)
                                .filter(worker=worker_id))

                    serializer = TaskSerializer(queryset, many=True)

                    response = JSendResponse(
                        status=JSendResponse.SUCCESS,
                        data=serializer.data
                    ).make_json()

                    return Response(response, status=status.HTTP_200_OK)

                else:
                    queryset = (Task.objects
                                .filter(
                                    order__client__company=request.user.company)
                                .filter(worker=worker_id))

                serializer = TaskSerializer(queryset, many=True)

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data=serializer.data
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            else:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': """You must have administrator \
                                    permissions to perform this action"""
                    }
                ).make_json()

                return Response(response, status=status.HTTP_403_FORBIDDEN)

        elif date or (date_start and date_end) or (year and month):
            # When neither worker nor particular task are specified,
            # default to my tasks
            if date:
                if (group_by_worker and
                        request.user.role.name == 'Administrator'):
                    # Tasks on a paricular day, grouped by workers
                    # TODO: = might not work here
                    queryset = (
                        Task.objects
                            .filter(
                                order__client__company=request.user.company)
                            .filter(starts_at=date))  # .values('worker')

                    # query.group_by = ['worker']
                    # queryset = QuerySet(query=query, model=Task)
                else:
                    # TODO: = might not work here
                    queryset = (Task.objects
                                .filter(worker=request.user.id)
                                .filter(starts_at=date))

            elif date_start and date_end:
                queryset = (Task.objects
                            .filter(
                                order__client__company=request.user.company)
                            .filter(worker=request.user.id)
                            .filter(starts_at__gte=date_start)
                            .filter(starts_at__lte=date_end))
            elif month and year:
                queryset = (Task.objects
                            .filter(
                                order__client__company=request.user.company)
                            .filter(worker=request.user.id)
                            .filter(starts_at__year=year)
                            .filter(starts_at__month=month))

            serializer = TaskSerializer(queryset, many=True)
            data = serializer.data

            if group_by_worker:
                data = json_list_group_by('worker_id', data)

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=data
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:
            # TODO: Check admin permissions properly using DRF permissions

            if request.user.role.name == 'Administrator':

                queryset = Task.objects.filter(
                    order__client__company=request.user.company)

                serializer = TaskSerializer(queryset, many=True)

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data=serializer.data
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            else:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': """You must have administrator \
                                    permissions to perform this action"""
                    }
                ).make_json()

                return Response(response, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, **kwargs):
        task_list = json.loads(request.data.get('task_list'))
        bulk_creation_result = bulk_create_tasks(task_list, request.user)

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'tasks': bulk_creation_result
            }
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):

        if 'id' not in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id in URL',
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        task_id = kwargs.get('id')

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': str(e)
                }
            ).make_json()
            return Response(response, status.HTTP_404_NOT_FOUND)

        if not task.order.client.company == request.user.company:

            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': """Task\'s company doesn\'t match \
                        the company of the request user"""
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            task = serializer.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Updated task {task.id} {task.name}',
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

        if 'id' not in kwargs:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'id': 'Must specify an id in URL',
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        task_id = kwargs.get('id')

        try:

            task = Task.objects.get(id=task_id)

            if not task.order.client.company == request.user.company:

                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': """Task\'s company doesn\'t match \
                                    the company of the request user"""
                    }
                ).make_json()

                return Response(response, status=status.HTTP_403_FORBIDDEN)

            taskName = task.name

            task.delete()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Successfully deleted task \
                                 {task_id} {taskName}'
                }
            ).make_json()

            return Response(response, status=status.HTTP_204_NO_CONTENT)

        except Task.DoesNotExist as e:

            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()

        return Response(response, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def accept_hours_worked(request, **kwargs):
    task_id = request.data.get('id')
    try:
        task = Task.objects.get(id=task_id)

        if not task.order.client.company == request.user.request.company:
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': 'This task belongs to another company \
                        than the request user\'s company'
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        if not task.is_hours_worked_accepted:
            task.is_hours_worked_accepted = True
            task.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Successfully accepted hours \
                        in task {task_id}'
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': (f"""Hours on task {task_id} \
                                 were already accepted \
                                 by an administrator""")
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

    except Task.DoesNotExist as e:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=str(e)
        ).make_json()
        return Response(response, status=status.HTTP_404_NOT_FOUND)


@required_kwargs(['id'])
def get_order_tasks(request, *args, **kwargs):
    order_id = kwargs['id']

    # TODO: getting and filtering can be moved into separate functions
    order = Order.objects.get(id=order_id)

    # TODO: move this check into a model logic or a permission
    if ((order.client.company == request.user.company
            and request.user.is_administrator())
       or request.user.is_staff):
        # TODO: getting and filtering can be moved into separate functions
        tasks_raw = Task.objects.filter(order=order_id)

        tasks = TaskSerializer(tasks_raw, many=True).data

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'tasks': tasks
            }
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)
    else:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': 'You cannot access this order\'s \
                    company information'
            }
        ).make_json()

        return Response(response, status=status.HTTP_403_FORBIDDEN)