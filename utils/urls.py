from django.urls import path
from django.conf.urls import url, include

from .views import (
    AddressView, FileView, get_presigned_upload_url, 
    model_files, my_files
)


app_name = 'utils'

address_list = AddressView.as_view()
file_list = FileView.as_view()

urlpatterns = [
    url(r'^addresses/?$', address_list),
    path('addresses/<int:id>', address_list),
    path('addresses/<int:id>/', address_list),

    url(r'^files/?$', file_list),
    path('files/<int:id>/', file_list),
    url(r'^users/me/files/?$', my_files),
    path('<str:model>/<int:id>/files/', model_files),

    url(r'get_upload_url/?$', get_presigned_upload_url),
]