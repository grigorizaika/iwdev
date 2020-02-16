import pyrebase

from django.shortcuts import render

def main_page(request):
    return render(request, 'main.html')

def handler404(request, *args, **argv):
    return render(request, '404.html', status=404)

def handler500(request, *args, **argv):
    return render(request, '500.html', status=500)


def signIn(request):
    return render(request, 'signIn.html')


def postSignIn(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    # user = auth.sign_in_with_email_and_password(email, password)

    return render(request, 'welcome.html', {'email': email})
