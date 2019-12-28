import django_filters.rest_framework
import firebase_admin

from api.serializers                import (AddressSerializer, ClientSerializer, UserSerializer, RegistrationSerializer)
from django.shortcuts               import get_object_or_404
from django.shortcuts               import render
from rest_framework                 import generics
from rest_framework                 import mixins
from rest_framework                 import permissions
from rest_framework                 import status
from rest_framework                 import viewsets
from rest_framework.authentication  import BasicAuthentication
from rest_framework.decorators      import (api_view, authentication_classes, permission_classes)
from rest_framework.permissions     import IsAuthenticated
from rest_framework.response        import Response
from rest_framework.views           import APIView

from utils.models                   import Address
from clients.models                 import Client
from inworkapi.settings             import FIREBASE_CONFIG
from api.permissions                import IsPostOrIsAuthenticated
from users.models                   import User as CustomUser
from users.models                   import Role
from utils.models                   import Address


class UserView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsPostOrIsAuthenticated]


    def get(self, request, **args):
        email = request.GET.get('email')
        queryset = CustomUser.objects.all()

        if email:
            user = get_object_or_404(queryset, email=email)
            serializer = UserSerializer(user)
        else:
            serializer = UserSerializer(queryset, many=True)

        return Response(serializer.data)

    def post(self, request, **args):
        serializer = RegistrationSerializer(data=request.data)
        data = {}  

        if serializer.is_valid():
            user = serializer.save()

            address = create_address(
                request.data.get('street'), 
                request.data.get('houseNo'), 
                request.data.get('city'), 
                request.data.get('district'), 
                request.data.get('country'), 
                request.data.get('flatNo'), 
            )     
            
            user.address = address
            user.save()

            data['response']    = 'Successfully registered a new user.'
            data['email']       = user.email
            data['name']        = user.name
        else:
            data = serializer.errors
   
        return Response(data)

    def patch(self, request, **args):
        print("in data of UserView, data: ", request.data)
        print("email: ", request.data['email'])
        
        email = request.data['email']

        djangoUser = CustomUser.objects.get(email=email)
        serializer = UserSerializer(djangoUser, data=request.data, partial=True)
        data = {}

        if serializer.is_valid():
            
            new_display_name = ''

            if request.data.get('name') and request.data.get('surname'):
                new_display_name = request.data.get('name') + ' ' + request.data.get('surname')
            elif request.data.get('name') and not request.data.get('surname'):
                new_display_name = request.data.get('name') + ' ' + djangoUser.surname
            elif not request.data.get('name') and request.data.get('surname'):
                new_display_name = djangoUser.name + ' ' + request.data.get('surname')
            else:
                new_display_name = djangoUser.name + ' ' + djangoUser.surname
            
            if request.data.get('phone'):
                firebaseUser = firebase_admin.auth.update_user(
                    djangoUser.firebaseId,
                    phone_number=request.data.get('phone'),
                )
            elif request.data.get('name') or request.data.get('surname'):
                firebaseUser = firebase_admin.auth.update_user(
                    djangoUser.firebaseId,
                    display_name=new_display_name,
                )

            djangoUser = serializer.save()
            data['response'] = 'Successfully updated user ' + str(email) + ' ' + str(new_display_name)
        else:
            data = serializer.errors

        return Response(data)

    def delete(self, request, email):
        
        print("In Users' DELETE, data: ", request.data)
        email = request.data.get('email')
        
        data = {}

        try:
            djangoUser = CustomUser.objects.get(email=email)

            firebase_admin.auth.delete_user(djangoUser.firebaseId)
            djangoUser.delete()

            data['response'] = "Successfully deleted " + str(email)

            return Response(data)
        except CustomUser.DoesNotExist:
            data['response'] = "User with an email " + str(email) + " does not exit"
            return Response(data)
        except Exception as e:
            data['response'] = "Unhandled exception " + e.message
   

class AddressView(generics.ListCreateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['street', 'city', 'district', 'country']

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


class ClientView(APIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, **args):

        email = request.GET.get('email')
        queryset = Client.objects.all()
        
        if email:
            client = get_object_or_404(queryset, email=email)
            serializer = ClientSerializer(client)
        else:
            serializer = ClientSerializer(queryset, many=True)

        return Response(serializer.data)

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

    def patch(self, request, **args):

        name = request.data.get('name')
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
        
        name = request.data.get('name')
        data = {}

        try:
            client = Client.objects.get(name=name)
            client.delete()
            data['response'] = "Successfully deleted " + str(name)
            return Response(data)
        except Client.DoesNotExist:
            data['response'] = "Client with a name " + str(name) + " does not exit"
            return Response(data)
        except Exception as e:
            data['response'] = "Unhandled exception " + e.message
   


def create_address(street, houseNo, city, district, country, flatNo=None,):
    return Address.objects.create(
        street=street,
        houseNo=houseNo,
        flatNo=flatNo,
        city=city,
        district=district,
        country=country
    )
