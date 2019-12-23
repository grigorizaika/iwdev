from django.conf.urls import url, include
from django.urls import path
from rest_framework import routers

from api.views import (AddressListView, api_user_view, ClientViewSet)

app_name = 'api'

router = routers.DefaultRouter()
#router.register(r'clients', ClientViewSet, basename='ClientViewSet')
#urlpatterns = router.urls
client_list     = ClientViewSet.as_view({'get': 'list'})
#client_detail   = ClientViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    url(r'users(?P<email>\w{0,50})', api_user_view, name="users"),
    url(r'addresses', AddressListView.as_view(), name="addresses"),
    url(r'clients(?P<email>\w{0,50})', client_list, name="clients"),
    #url(r'fuckinhell', client_detail, name="clients_detail"),
]

urlpatterns += router.urls