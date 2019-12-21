from django.conf.urls import url, include
from django.urls import path
from rest_framework import routers

from api.views import (AddressListView, api_user_view, ClientListView)

app_name = 'api'


router = routers.SimpleRouter()
#router.register(r'addresses', AddressListView, basename="AddressListView")
#router.register(r'user_detail', api_detail_user_view, basename="api_detail_user_view")


urlpatterns = [
    url(r'users(?P<email>\w{0,50})', api_user_view, name="users"),
    url(r'addresses', AddressListView.as_view(), name="addresses"),
    url(r'clients', ClientListView.as_view(), name="addresses"),
]

urlpatterns += router.urls
