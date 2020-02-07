from api.views import (accept_hours_worked, change_password, client_addresses,
                        confirm_sign_up, confirm_reset_password, FileView, 
                        get_current_user, AddressView, ClientView, CompanyView,
                        check_phone, get_jwt_tokens, get_presigned_upload_url, 
                        initiate_reset_password, initiate_verify_attribute, model_files,
                        my_files, OrderView, refresh_jwt_tokens, resend_confirmation_code, 
                        TaskView, UserView, verify_attribute)
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
file_list = FileView.as_view()
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
    url(r'^addresses/$', address_list),
    path('addresses/<int:id>/', address_list),
    url(r'^files/$', file_list),
    path('files/<int:id>/', file_list),
    url(r'clients/$', client_list),
    path('clients/<int:id>/', client_list),
    path('clients/<int:id>/addresses/', client_addresses),
    url(r'^users/$', user_list),
    url(r'^users/me/$', get_current_user),
    path('users/<int:id>/', user_list),
    url(r'users/check_phone(?P<phone>\w{0,50})/$', check_phone),
    url(r'orders/$', order_list),
    path('orders/<int:id>/', order_list),
    url(r'tasks/$', task_list),
    path('tasks/<int:id>/', task_list),
    url(r'tasks/accept_hours/$', accept_hours_worked),
    path('companies/', company_list),
    path('companies/<int:id>/', company_list),
    
    url(r'get_upload_url/$', get_presigned_upload_url),
    #url(r'check_phone(?P<phone>\w{0,50})/$', user_list, name="check_phone"),
    #url(r'users/register', user_registration, name="registration"),
    url(r'get_tokens(?P<username>\w{0,50})(?P<password>\w{0,50})/$', get_jwt_tokens),
    url(r'refresh_tokens/$', refresh_jwt_tokens),
    url(r'change_password/$', change_password),
    url(r'initiate_reset_password/$', initiate_reset_password),
    url(r'confirm_reset_password/$', confirm_reset_password),
    path('users/<int:id>/resend_confirmation_code/', resend_confirmation_code),
    url(r'confirm_sign_up/$', confirm_sign_up),
    url(r'^verify_attribute/$', verify_attribute),
    url(r'^initiate_verify_attribute/$', initiate_verify_attribute),
    
    path('<str:model>/<int:id>/files/', model_files),
    url(r'^users/me/files/$', my_files),
]
