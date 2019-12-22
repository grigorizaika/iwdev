from django.contrib.auth import get_user_model
from drf_firebase.authentication import BaseFirebaseAuthentication
from firebase_admin import credentials, initialize_app
from inworkapi.settings import FIREBASE_KEY
from rest_framework import authentication

firebase_creds = credentials.Certificate(FIREBASE_KEY)
firebase_app = initialize_app(firebase_creds)

class FirebaseAuthentication(BaseFirebaseAuthentication):

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        print('Authorization header: ', auth)
        BaseFirebaseAuthentication.authenticate(self, request)

    def get_firebase_app(self):
        return firebase_app

    def get_django_user(self, firebase_user_record):
	    return get_user_model().objects.get_or_create(
		    firebaseId=firebase_user_record.uid,
	    )[0]