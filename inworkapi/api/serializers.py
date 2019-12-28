from rest_framework import serializers

from users.models import User as CustomUser
from users.models import Role
from utils.models import Address
from clients.models import Client

class RegistrationSerializer(serializers.ModelSerializer):
    password2   = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'surname', 'phone', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def save(self):

        user = CustomUser.objects.create_user(
            email       = self.validated_data['email'],
            name        = self.validated_data['name'],
            surname     = self.validated_data['surname'],
            phone       = self.validated_data['phone'],
        )
        
        password    = self.validated_data['password']
        password2   = self.validated_data['password2']

        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords don\'t match'})

        user.password   = password
        user.save()

        return user

    def update(self, instance, validated_data):
        print("in UserSerializer's update")
        instance.name       = validated_data['name']
        instance.surname    = validated_data['surname']
        instance.phone      = validated_data['phone']
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    address = serializers.StringRelatedField()

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email    = validated_data['email'], 
            name     = validated_data['name'], 
            surname  = validated_data['surname'], 
            phone    = validated_data['phone'], 
            password = validated_data['password'],
        )
        user.role    = validated_data['role']


    class Meta:
        model = CustomUser
        exclude = ('password', 'last_login', 'is_staff', 'is_superuser')
        # fields = ('email', 'name', 'surname', 'phone', 'address', 'role', 'supervisor')
        

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

    def create(self, validated_data):
        print('In save(), ', validated_data)
        return Client.objects.create(
            name            = validated_data['name'], 
            email           = validated_data['email'], 
            contactName     = validated_data['contactName'], 
            contactPhone    = validated_data['contactPhone']
        )

    #def update(self, instance, validated_data):
        #instance.name       = validated_data['name']
        #instance.surname    = validated_data['surname']
        #instance.phone      = validated_data['phone']
        #instance.save()
        #return instance
    

