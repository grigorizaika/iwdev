import django_filters.rest_framework

from api.serializers            import (AddressSerializer, ClientSerializer, UserSerializer, RegistrationSerializer)
from django.shortcuts           import get_object_or_404
from django.shortcuts           import render
from rest_framework             import generics
from rest_framework             import mixins
from rest_framework             import permissions
from rest_framework             import status
from rest_framework             import viewsets
from rest_framework.decorators  import api_view
from rest_framework.response    import Response

from clients.models             import Client
from users.models               import User as CustomUser
from users.models               import Role
from utils.models               import Address


# VIEWS

@api_view(['POST',])
def registration_view(request):
    
    serializer = RegistrationSerializer(data=request.data)
    
    data = {}

    if serializer.is_valid():
        user = serializer.save()
        data['response']    = 'Successfully registered a new user.'
        data['email']       = user.email
        data['name']        = user.name
    else:
        data = serializer.errors
    
    return Response(data)

#@api_view(['GET',])
#def api_user_view(request, email):
    # TODO: Why should it be both here and in the argument list?
    #email = request.GET.get('email')
#
    #if email is None:
        #queryset = CustomUser.objects.all()
        #serializer = UserSerializer(queryset, many=True)
        #return Response(serializer.data)
#
    #try:
        #user = CustomUser.objects.get(email=email)
        #serializer = UserSerializer(user)
        #return Response(serializer.data, status=status.HTTP_200_OK)
    #except CustomUser.DoesNotExist:
        #return Response({"email": email}, status=status.HTTP_404_NOT_FOUND)


class AddressListView(generics.ListAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['street', 'city', 'district', 'country']

#class ClientListView(generics.ListAPIView):
#    queryset = Client.objects.all()
#    serializer_class = ClientSerializer
#    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
#    filterset_fields = ['name', 'email']
#    permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ViewSet):

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    
    def list(self, request, **args):
        
        email = request.GET.get('email')
        queryset = CustomUser.objects.all()

        if email:
            user = get_object_or_404(queryset, email=email)
            serializer = UserSerializer(user)
        else:
            serializer = UserSerializer(queryset, many=True)

        return Response(serializer.data)


class ClientViewSet(mixins.ListModelMixin, viewsets.ViewSet):

    def list(self, request, **args):
        
        email = request.GET.get('email')
        queryset = Client.objects.all()
        
        if email:
            client = get_object_or_404(queryset, email=email)
            serializer = ClientSerializer(client)
        else:
            serializer = ClientSerializer(queryset, many=True)

        return Response(serializer.data)