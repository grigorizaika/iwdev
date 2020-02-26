from django.urls import path
from django.conf.urls import url, include

from .views import (
    UserView, CompanyView, check_phone, get_current_user, 
    change_password, initiate_reset_password, confirm_reset_password, 
    confirm_sign_up, initiate_verify_attribute, admin_create_cognito_user,
    respond_to_new_password_required_challenge, verify_attribute,
    resend_confirmation_code
)



app_name = 'users'

company_list = CompanyView.as_view()
user_list = UserView.as_view()

urlpatterns = [
    url(r'^users/?$', user_list),
    url(r'^users/me/?$', get_current_user),
    # TODO: parameter -> keyword
    url(r'^users/check_phone(?P<phone>\w{0,50})/?$', check_phone),
    url(r'^users/change_password/?$', change_password),
    url(r'^users/initiate_reset_password/?$', initiate_reset_password),
    url(r'^users/confirm_reset_password/?$', confirm_reset_password),
    url(r'^users/confirm_sign_up/?$', confirm_sign_up),
    url(r'^users/initiate_verify_attribute/?$', initiate_verify_attribute),
    url(r'^users/verify_attribute/?$', verify_attribute),
    url(r'^users/register_user/?$', admin_create_cognito_user),
    url(r'^users/respond_to_new_password_challenge/?$', respond_to_new_password_required_challenge),
    path('users/<int:id>/', user_list),
    path('users/<int:id>/resend_confirmation_code/', resend_confirmation_code),

    path('companies/', company_list),
    path('companies/<int:id>/', company_list),
]