from django.shortcuts import render
import pyrebase

# TODO: Switch firebase accounts later
firebaseConfig = {
    'apiKey': 'AIzaSyDV00d68812eZuIoCMKKX27w7tEGs_1Bwg',
    'authDomain': 'inworktest.firebaseapp.com',
    'databaseURL': 'https://inworktest.firebaseio.com',
    'projectId': 'inworktest',
    'storageBucket': 'inworktest.appspot.com',
    'messagingSenderId': '111246495065',
    'appId': '1:111246495065:web:f4a63df5719dd825e41048'
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()

def signIn(request):
    return render(request, 'signIn.html')

def postSignIn(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    user = auth.sign_in_with_email_and_password(email, password)
    
    return render(request, 'welcome.html', { "email": email })