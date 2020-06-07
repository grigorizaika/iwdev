import botocore
from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import generics, mixins, status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Absence, Company, Role, User as CustomUser
from .serializers import (AbsenceSerializer, CompanySerializer,
                          PasswordSerializer, RegistrationSerializer,
                          UserSerializer)
from api.helpers import generate_temporary_password
from api.permissions import IsAdministrator, IsAuthenticated
from inworkapi.decorators import (
    required_body_params, admin_body_params, required_kwargs)
from inworkapi.utils import JSendResponse, CognitoHelper
from utils.serializers import AddressSerializer


@api_view(['GET'])
def check_phone(request, **kwargs):
    # TODO: restrict by the number of requests from the same IP

    if 'phone' not in request.query_params:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'phone': 'Phone number has not been provided'
            }
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    phone = '+' + request.query_params['phone'][1:]

    try:
        CustomUser.objects.get(phone=phone)

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': True
            }
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)

    except CustomUser.DoesNotExist:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': False
            }
        ).make_json()
        return Response(response, status=status.HTTP_200_OK)


@api_view(['GET'])
# @authentication_classes([JSONWebTokenAuthentication])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=serializer.data
    ).make_json()
    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['old_password', 'new_password', 'access_token'])
def change_password(request, **kwargs):
    user = request.user

    serializer = PasswordSerializer(data=request.data)

    if serializer.is_valid():
        if check_password(serializer.data['old_password'], user.password):
            client = CognitoHelper.get_client()

            try:
                cognito_response = client.change_password(
                    PreviousPassword=serializer.data['old_password'],
                    ProposedPassword=serializer.data['new_password'],
                    AccessToken=request.data['access_token'])
            except client.exceptions.NotAuthorizedException as e:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data=str(e)
                ).make_json()
                return Response(response, status=status.HTTP_401_UNAUTHORIZED)

            user.set_password(serializer.data['new_password'])
            user.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': cognito_response
                }
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': 'Old password didn\'t match'
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

    else:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=serializer.errors
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
def initiate_reset_password(request, **kwargs):
    client = CognitoHelper.get_client()

    cognito_response = client.forgot_password(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(request.user.email))

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['new_password', 'confirmation_code'])
def confirm_reset_password(request, **kwargs):

    user = request.user

    client = CognitoHelper.get_client()

    cognito_response = client.confirm_forgot_password(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=str(user.email),
        ConfirmationCode=str(request.data['confirmation_code']),
        Password=str(request.data['new_password']),
    )

    user.set_password(str(request.data['new_password']))
    user.save()

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_kwargs
def resend_confirmation_code(request, **kwargs):
    response = {}

    try:
        user = CustomUser.objects.get(id=kwargs.get('id'))
    except CustomUser.DoesNotExist as e:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=str(e)
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    if (request.user.is_administrator()
            or request.user.id == kwargs.get('id')):
        client = CognitoHelper.get_client()

        cognito_response = client.resend_confirmation_code(
            ClientId=settings.COGNITO_APP_CLIENT_ID,
            Username=str(user.email))

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=cognito_response
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)

    response = JSendResponse(
        status=JSendResponse.FAIL,
        data={
            'response': '''Must be administrator or self \
                to perform this action'''
        }
    ).make_json()

    return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@required_body_params(['confirmation_code', 'email'])
def confirm_sign_up(request, **kwargs):

    client = CognitoHelper.get_client()

    cognito_response = client.confirm_sign_up(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=request.data['email'],
        ConfirmationCode=request.data['confirmation_code'],
    )

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['access_token', 'attribute_name'])
def initiate_verify_attribute(request, **kwargs):

    available_attribute_names = ['email', 'phone_number']

    if request.data['attribute_name'] not in available_attribute_names:

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f'''Possible attribute_name \
                    values are: {available_attribute_names}'''
            }
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    client = CognitoHelper.get_client()

    cognito_response = client.get_user_attribute_verification_code(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
    )

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@required_body_params(['access_token', 'attribute_name', 'confirmation_code'])
def verify_attribute(request, **kwargs):

    available_attribute_names = ['email', 'phone_number']

    if request.data['attribute_name'] not in available_attribute_names:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': f'''Possible attribute_name \
                    values are: {available_attribute_names}'''
            }
        ).make_json()
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    client = CognitoHelper.get_client()

    cognito_response = client.verify_user_attribute(
        AccessToken=request.data['access_token'],
        AttributeName=request.data['attribute_name'],
        Code=request.data['confirmation_code'],
    )

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data=cognito_response
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)

# Admin registration flow
@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAdministrator])
@required_body_params(['email', 'phone_number', 'name', 'surname'])
def admin_create_cognito_user(request, **kwargs):
    # TODO: the name is misleading, change it

    email = request.data['email']
    phone_number = request.data['phone_number']
    name = request.data['name']
    surname = request.data['surname']
    temporary_password = request.data.get(
        'temporary_password', generate_temporary_password())

    client = CognitoHelper.get_client()
    try:
        cognito_response = client.admin_create_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=str(email),
            UserAttributes=[
                {'Name': 'email', 'Value': str(email)},
                {'Name': 'email_verified', 'Value': 'True'},
                {'Name': 'phone_number', 'Value': str(phone_number)},
            ],
            TemporaryPassword=temporary_password,
            DesiredDeliveryMediums=['EMAIL'],
        )

    except botocore.exceptions.ParamValidationError as e:
        response = JSendResponse(
            status=JSendResponse.ERROR,
            message=str(e)
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    sub = next(attribute['Value'] for attribute
               in cognito_response['User']['Attributes']
               if attribute['Name'] == 'sub')

    user_data = {
        'name': name,
        'surname': surname,
        'phone': phone_number,
        'email': email,
        'password': temporary_password,
        'password2': temporary_password,
    }

    serializer = RegistrationSerializer(
        data=user_data, create_cognito_user=False)

    if serializer.is_valid():

        user = serializer.save()

        worker_role, created = Role.objects.get_or_create(name='Worker')

        user.role = worker_role
        user.company = request.user.company
        user.supervisor = request.user
        user.cognito_id = sub

        user.save()

    else:
        client.admin_delete_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=str(email))

        response = JSendResponse(
            status=JSendResponse.FAIL,
            data=serializer.errors
        ).make_json()

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data={
            'response': cognito_response,
            'user': UserSerializer(user).data,
            'temporary_password': temporary_password
        }
    ).make_json()

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@required_body_params(['new_password', 'session', 'email'])
def respond_to_new_password_required_challenge(request, **kwargs):
    email = request.data['email']
    new_password = request.data['new_password']
    session = request.data['session']

    client = CognitoHelper.get_client()

    cognito_response = client.respond_to_auth_challenge(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        ChallengeName='NEW_PASSWORD_REQUIRED',
        Session=session,
        ChallengeResponses={
            'USERNAME': str(email),
            'NEW_PASSWORD': new_password
        },
    )

    try:
        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()

    except CustomUser.DoesNotExist as e:
        response = JSendResponse(
            status=JSendResponse.FAIL,
            data={
                'response': str(e),
                'user': None
            }
        ).make_json()
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    response = JSendResponse(
        status=JSendResponse.SUCCESS,
        data={
            'cognito_response': cognito_response,
            'user': UserSerializer(user).data
        }
    ).make_json()
    return Response(response, status=status.HTTP_200_OK)


class UserView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAdministrator]

    def get(self, request, *args, **kwargs):
        # get list
        if 'id' not in kwargs:
            if not (request.user.is_administrator()
                    or request.user.is_staff):
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'id': 'Only administrators can see worker lists'
                    }
                ).make_json()
                return Response(response, status=status.HTTP_403_FORBIDDEN)
            elif request.user.is_administrator():
                queryset = CustomUser.objects.filter(
                    company=request.user.company)
            elif request.user.is_staff:
                queryset = CustomUser.objects.all()

            serializer = UserSerializer(queryset, many=True)

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data=serializer.data
            ).make_json()

            return Response(response, status=status.HTTP_200_OK)

        # get instance
        queryset = CustomUser.objects.filter(company=request.user.company)

        try:
            user = queryset.get(id=kwargs.get('id'))

        except CustomUser.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if user.company != request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': '''User\'s company doesn\'t match \
                        the request user\'s company'''
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(user)

        response = JSendResponse(
            status=JSendResponse.SUCCESS,
            data=serializer.data
        ).make_json()

        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        processed_data = request.data.dict()

        if processed_data.get('role'):
            del processed_data['role']

        serializer = RegistrationSerializer(data=processed_data)

        if serializer.is_valid():
            user = serializer.save()
            worker_role, _ = Role.objects.get_or_create(name='Worker')

            user.role = worker_role
            user.company = request.user.company

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

                addressSerializer.save()

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'id': user.id
                    }
                ).make_json()

                return Response(response, status=status.HTTP_200_OK)

            else:

                response = JSendResponse(
                    status=JSendResponse.SUCCESS,
                    data={
                        'response': '''Successfully registered a new user,\
                            but address parameters were invalid.''',
                        'detail': addressSerializer.errors,
                        'id': user.id
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
        # Check if admin or self

        processed_data = request.data.dict()

        if 'role' in processed_data:
            # Role is not allowed to be
            # changed with PATCH request
            processed_data.pop('role')

        if 'profile_picture_url' in processed_data:
            processed_data['profile_picture_url'] = str(
                processed_data['profile_picture_url'])

        if 'email' in processed_data:
            processed_data.pop('email')

        djangoUser = CustomUser.objects.get(id=kwargs['id'])

        if djangoUser.company != request.user.company:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={
                    'response': '''User\'s company doesn\'t \
                        match the request user\'s company'''
                }
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(
            djangoUser, data=processed_data, partial=True)

        if serializer.is_valid():
            djangoUser = serializer.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Successfully updated user {djangoUser.email}'
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
    def delete(self, request, **kwargs):
        # TODO: also delete addresses

        try:
            djangoUser = CustomUser.objects.get(id=kwargs.get('id'))

            if not djangoUser.company == request.user.company:
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'response': '''User\'s company doesn\'t \
                            match the request user\'s company'''
                    }
                ).make_json()

                return Response(response, status=status.HTTP_403_FORBIDDEN)

            djangoUser.delete()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={}
            ).make_json()

            return Response(response, status=status.HTTP_204_NO_CONTENT)

        except CustomUser.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)


class AbsenceView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_list(self, whos_asking, want_serialized=False):
        if whos_asking.is_superuser:
            absences = Absence.objects.all()
        elif whos_asking.is_administrator():
            absences_same_company = Absence.objects.filter(
                user__company=whos_asking.company)
            absences = absences_same_company
        else:
            absences_same_user = Absence.objects.filter(
                user=whos_asking)
            absences = absences_same_user

        return (AbsenceSerializer(absences, many=True).data
                if want_serialized else absences)

    def get_instance(self, id, whos_asking, want_serialized=False):
        if whos_asking.is_superuser:
            absence = Absence.objects.get(id=id)
        elif whos_asking.is_administrator():
            absences_same_company = Absence.objects.filter(
                user__company=whos_asking.company)
            absence = absences_same_company.get(id=id)
        else:
            absences_same_user = Absence.objects.filter(
                user=whos_asking)
            absence = absences_same_user.get(id=id)

        return (AbsenceSerializer(absence).data
                if want_serialized else absence)

    def get(self, request, *args, **kwargs):
        if 'id' not in kwargs:
            absence_list = self.get_list(
                whos_asking=request.user, want_serialized=True)
            response = JSendResponse(
                status=JSendResponse.SUCCESS, data=absence_list).make_json()
            return Response(response, status=status.HTTP_200_OK)

        try:
            absence = self.get_instance(
                kwargs['id'], whos_asking=request.user, want_serialized=True)
            response = JSendResponse(
                status=JSendResponse.SUCCESS, data=absence).make_json()
            return Response(response, status=status.HTTP_200_OK)

        except Absence.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL, data=str(e)).make_json()
            return Response(
                response, status=status.HTTP_404_NOT_FOUND)

    @admin_body_params(['user', 'state'])
    def post(self, request, *args, **kwargs):
        processed_data = request.data.dict()

        if 'user' not in processed_data:
            processed_data['user'] = request.user.id

        absence_serializer = AbsenceSerializer(data=processed_data)

        if absence_serializer.is_valid():
            absence = absence_serializer.save()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Created {absence}',
                    'id': absence.id
                }
            ).make_json()

            return Response(response, status=status.HTTP_201_CREATED)

        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=absence_serializer.errors).make_json()
            return Response(
                response, status=status.HTTP_400_BAD_REQUEST)

    @required_kwargs(['id'])
    @admin_body_params(['user', 'state'])
    def patch(self, request, *args, **kwargs):
        try:
            absence = self.get_instance(
                kwargs['id'],
                whos_asking=request.user,
                want_serialized=False)

            if (not absence.state == 'Pending'
                    and not request.user.is_administrator()):
                response = JSendResponse(
                    status=JSendResponse.FAIL,
                    data={
                        'absence': '''absence can\'t be changed by \
                                    workers once it\'s been confirmed'''
                    }
                ).make_json()
                return Response(response, status=status.HTTP_403_FORBIDDEN)

        except Absence.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        absence_serializer = AbsenceSerializer(
            absence, data=request.data, partial=True)

        if absence_serializer.is_valid():
            absence = absence_serializer.save()
            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={
                    'response': f'Updated {absence}'
                }
            ).make_json()
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=absence_serializer.errors
            ).make_json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @required_kwargs(['id'])
    def delete(self, request, *args, **kwargs):
        if not (request.user.is_administrator() or request.user.is_superuser):
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data={'user': 'Only an administrator can delete absences.'}
            ).make_json()
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        try:
            absence = self.get_instance(
                kwargs['id'],
                whos_asking=request.user,
                want_serialized=False)

            absence.delete()

            response = JSendResponse(
                status=JSendResponse.SUCCESS,
                data={}
            ).make_json()

            return Response(response, status=status.HTTP_204_NO_CONTENT)

        except Absence.DoesNotExist as e:
            response = JSendResponse(
                status=JSendResponse.FAIL,
                data=str(e)
            ).make_json()
            return Response(response, status=status.HTTP_404_NOT_FOUND)


class CompanyView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # TODO: JSendResponse format
