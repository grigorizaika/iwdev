import pyrebase

from django.shortcuts import render
# from inworkapi.settings import FIREBASE_CONFIG


# firebase = pyrebase.initialize_app(FIREBASE_CONFIG)

# auth = firebase.auth()


def signIn(request):
    return render(request, 'signIn.html')


def postSignIn(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    # user = auth.sign_in_with_email_and_password(email, password)

    return render(request, 'welcome.html', {'email': email})
