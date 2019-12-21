from rest_framework import serializers

from users.models import User as CustomUser
from users.models import Role
from utils.models import Address
from clients.models import Client

class UserSerializer(serializers.ModelSerializer):
    address = serializers.StringRelatedField()

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