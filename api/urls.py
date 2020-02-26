from django.conf.urls import url, include
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework import routers

from api.views import get_jwt_tokens, refresh_jwt_tokens



app_name = 'api'

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
    url(r'^$', schema_view),
    url(
        r'^swagger/?$', 
        schema_view.with_ui('swagger', cache_timeout=0), 
        name='schema-swagger-ui'
    ),

    path('', include('utils.urls', namespace='utils')),
    path('clients/', include('clients.urls', namespace='clients')),
    path('', include('users.urls', namespace='users')),
    path('', include('orders.urls', namespace='orders')),
           
    url(r'get_tokens(?P<username>\w{0,50})(?P<password>\w{0,50})/?$', get_jwt_tokens),
    url(r'refresh_tokens/?$', refresh_jwt_tokens),
]
