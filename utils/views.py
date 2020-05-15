import django.apps
from django_cognito_jwt import JSONWebTokenAuthentication
from rest_framework import status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Address, AddressOwner, CustomFile
from .serializers import AddressSerializer, FileSerializer
from api.permissions import IsAdministrator
from inworkapi.decorators import required_body_params, required_kwargs
from inworkapi.utils import JSendResponse, S3Helper


@api_view(['GET'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
@required_body_params(['to', 'id', 'file_name'])
def get_presigned_upload_url(request, **kwargs):

    location = request.data['to']
    file_name = request.data['file_name']

    # TODO: decorator
    if location not in S3Helper.KEY_TO_MODEL_MAPPING.keys():
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f"""location should be one of \
                    the following values: \
                    {S3Helper.KEY_TO_MODEL_MAPPING.keys()}"""
            }
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    if (location == 'users'
        and not (request.user.is_administrator()
                 or request.user.is_staff)):

        if ('id' in request.data
                and request.data['id'] != request.user.id):
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={'id': """Only administrators can \
                    add files to users other than themselves."""}
            )
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        object_name = f'{location}/{request.user.id}/{file_name}'
    else:
        # TODO: allow upload to client only if admin is assigned to the client
        if 'id' not in request.data:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': f'Must specify {location[:-1]} id'
                }
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        resource_id = request.data['id']
        object_name = f'{location}/{resource_id}/{file_name}'

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data={
            'response': S3Helper.create_presigned_put(object_name)
        }
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
def model_files(request, **kwargs):

    all_model_classess = {
        model_class.__name__: model_class
        for model_class in django.apps.apps.get_models()
        }

    possible_model_values = {
        model_key: model_class
        # S3Helper.KEY_TO_MODEL_MAPPING lists names
        # of models that can have files
        for model_key in S3Helper.KEY_TO_MODEL_MAPPING.keys()
        # all_model_classes are used here to convert
        # model class name strings from above to class format
        for model_class in all_model_classess.values()
        if (model_class.__name__
            == S3Helper.KEY_TO_MODEL_MAPPING[model_key])
    }

    if ('model' not in kwargs or 'id' not in kwargs):
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': """Proper URL structure: \
                    /api/<string:model>/<int:id>/files/"""
            }
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    if not kwargs['model'] in list(possible_model_values.keys()):
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f"""\'model\' must be \
                    one of these values: \
                    { list(possible_model_values.keys()) }"""
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
                    'response': f"""{model.__name__} with \
                        an id {instance_id} does not exist"""
                }
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)

        fo = instance.file_owner

        processed_data = request.data.dict()

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
                    'response': f"""{model.__name__} with an id \
                        {instance_id} does not exist"""
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

        if 'id' not in kwargs:
            # TODO: restrict addresses for users
            # make this filtering in Adress model
            addresses = Address.objects.all()
            serializer = AddressSerializer(addresses, many=True)
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()
            return Response(response, status=status.HTTP_200_OK)

        address_id = kwargs.get('id')

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if address.owner.get_owner_instance().company != request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': '''Addresses\' owner company doesn\'t \
                        match your company'''
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = AddressSerializer(address)

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data=serializer.data
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        if 'owner' in request.data:
            ao = AddressOwner.objects.get(id=request.data['owner'])
            owner_instance = ao.get_owner_instance()

            if owner_instance.company != request.user.company:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': '''Owner\'s company doesn\'t \
                            match your company'''
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

    @required_kwargs(['id'])
    def patch(self, request, **kwargs):
        address_id = kwargs.get('id')

        try:
            address = Address.objects.get(id=address_id)
            owner_instance = address.owner.get_owner_instance()
        except Address.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()

            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if owner_instance.company != request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': 'Owner\'s company doesn\'t match your company'
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = AddressSerializer(address,
                                       data=request.data,
                                       partial=True)

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

    @required_kwargs(['id'])
    def delete(self, request, *args, **kwargs):
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
                data={
                    'response': 'Owner\'s company doesn\'t match your company'
                }
            ).make_json()

            return Response(response, status=status.HTTP_403_FORBIDDEN)

        address_str = str(address)

        address.delete()

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'response': f'Successfully deleted address {address_str}'
            }
        ).make_json()

        return Response(response, status=status.HTTP_204_NO_CONTENT)


class FileView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]

    def get(self, request, *args, **kwargs):

        if 'id' not in kwargs:
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

        if 'id' not in kwargs:
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

        if 'id' not in kwargs:
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

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data={
                'response': f'Successfully deleted file {file_str}'
            }
        ).make_json()

        return Response(response, status=status.HTTP_204_NO_CONTENT)