from django.urls import path
from django.conf.urls import url, include

from .views import ClientView, client_addresses



app_name = 'clients'

client_list = ClientView.as_view()

urlpatterns = [
    url(r'^$', client_list),
    path('<int:id>/', client_list),
    path('<int:id>/addresses/', client_addresses),
]