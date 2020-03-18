import pyrebase

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response

from inworkapi.utils import JSendResponse


def main_page(request):
    return render(request, 'main.html')

def handler404(request, *args, **argv):
    response = JSendResponse(
        status=JSendResponse.ERROR,
        data='404 page not found'
    ).make_json()
    return JsonResponse(response, status=status.HTTP_404_NOT_FOUND)

def handler500(request, *args, **argv):
    response = JSendResponse(
        status=JSendResponse.ERROR,
        data='500 internal server error'
    ).make_json()
    return JsonResponse(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def signIn(request):
    return render(request, 'signIn.html')

def postSignIn(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    # user = auth.sign_in_with_email_and_password(email, password)

    return render(request, 'welcome.html', {'email': email})
