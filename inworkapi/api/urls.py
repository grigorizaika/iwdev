from django.conf.urls import url, include
from django.urls import path
from rest_framework import routers

from api.views import (AddressListView, ClientViewSet, UserViewSet, registration_view)

app_name = 'api'

address_list    = AddressListView.as_view()
client_list     = ClientViewSet.as_view({ 'get': 'list' })
user_list       = UserViewSet.as_view({ 'get': 'list' })

urlpatterns = [
    url(r'addresses', address_list, name="addresses"),
    url(r'clients(?P<email>\w{0,50})', client_list, name="clients"),
    url(r'users(?P<email>\w{0,50})', user_list, name="users"),
    url(r'register', registration_view, name="registration"),
]