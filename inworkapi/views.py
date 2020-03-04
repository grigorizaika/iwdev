import pyrebase

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response

def main_page(request):
    return render(request, 'main.html')

def handler404(request, *args, **argv):
    response = {}
    response['status'] = 'fail'
    response['data'] = '404 page not found'
    return JsonResponse(response)

def handler500(request, *args, **argv):
    response = {}
    response['status'] = 'fail'
    response['data'] = '500 internal server error'
    return JsonResponse(response)

def signIn(request):
    return render(request, 'signIn.html')


def postSignIn(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    # user = auth.sign_in_with_email_and_password(email, password)

    return render(request, 'welcome.html', {'email': email})
