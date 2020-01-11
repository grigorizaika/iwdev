from api.views import (AddressView, ClientView, CompanyView, check_phone, get_presigned_url, OrderView, TaskView, UserView,)
from django.conf.urls import url, include
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework import routers

app_name = 'api'

address_list = AddressView.as_view()
client_list = ClientView.as_view()
company_list = CompanyView.as_view()
order_list = OrderView.as_view()
task_list = TaskView.as_view()
user_list = UserView.as_view()

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    #url(r'^$', schema_view),
    url(r'^swagger/$', schema_view.with_ui('swagger',
                                           cache_timeout=0), name='schema-swagger-ui'),
    url(r'addresses', address_list, name="addresses"),
    url(r'clients(?P<name>\w{0,50})/$', client_list, name="clients"),
    url(r'users(?P<email>\w{0,50})/$', user_list),
    url(r'users/check_phone(?P<phone>\w{0,50})/$', check_phone),
    url(r'orders(?P<id>\w{0,50})/$', order_list),
    url(r'tasks(?P<id>\w{0,50})/$', task_list),
    url(r'companies(?P<id>\w{0,50})/$', company_list),
    url(r'get_upload_url/$', get_presigned_url)
    #url(r'check_phone(?P<phone>\w{0,50})/$', user_list, name="check_phone"),
    #url(r'users/register', user_registration, name="registration"),
]
