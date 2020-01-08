from rest_framework import serializers

from clients.models import Client
from orders.models import (Order, Task)
from users.models import User as CustomUser
from users.models import (Company, Role)
from utils.models import (Address, AddressOwner)


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)


    def create(self, validated_data):
        password = validated_data['password']
        password2 = validated_data['password2']

        if password != password2:
            raise serializers.ValidationError(
                {'password': 'Passwords don\'t match'})
        
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            phone=validated_data['phone'],
            password=password
        )

        user.save()
        
        return user


    def update(self, instance, validated_data):
        print("in UserSerializer's update")
        instance.name = validated_data['name']
        instance.surname = validated_data['surname']
        instance.phone = validated_data['phone']
        instance.save()
        return instance

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'surname', 'phone', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    

class UserSerializer(serializers.ModelSerializer):
    address_owner = serializers.StringRelatedField()
    addresses = serializers.SerializerMethodField()


    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            phone=validated_data['phone'],
            password=validated_data['password'],
        )
        user.role = validated_data['role']
        return user


    def get_addresses(self, obj):
        queryset = obj.addresses()
        print('HERE HERE HERE HERE HERE ' + str(type(queryset)))
        print('HERE HERE HERE HERE HERE ' + str(queryset))
        serializer = AddressSerializer(queryset, many=True)
        return serializer.data


    class Meta:
        model = CustomUser
        exclude = ('password', 'last_login', 'is_staff', 'is_superuser')
        # fields = ('email', 'name', 'surname', 'phone', 'address', 'role', 'supervisor')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class AddressOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressOwner
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    owner_email = serializers.SerializerMethodField()
    owner_class = serializers.SerializerMethodField()


    def get_owner_class(self, obj):
        return obj.get_owner_instance().__class__.__name__


    def get_owner_email(self, obj):
        return obj.get_owner_instance().email


    class Meta:
        model = Address
        #fields = '__all__'
        fields = [
            'id', 'street', 'house_no', 'flat_no', 'city', 'district', 
            'country', 'postal_code', 'owner', 'owner_email', 'owner_class'
        ]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


    def create(self, validated_data):
        return Client.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            contactName=validated_data['contactName'],
            contactPhone=validated_data['contactPhone']
        )


class OrderSerializer(serializers.ModelSerializer):
    #client  = serializers.StringRelatedField()
    address = serializers.StringRelatedField()


    def create(self, validated_data):
        print ("In Order create(): ", validated_data)
        return Order.objects.create(
            name = validated_data['name'],
            client = validated_data['client'],
            #address = validated_data['address'],
            billingPeriod = validated_data['billingPeriod'],
            description = validated_data['description'],
        )


    class Meta:
        model = Order
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):


    def create(self, validated_data):
        print("In Task create(): ", validated_data)
        return Task.objects.create(
            order=validated_data['order'],
            name=validated_data['name'],
            date=validated_data['date'],
            manualTimeSet=validated_data['manualTimeSet'],
            worker=validated_data['worker'],
            description=validated_data['description'],
            comment=validated_data['comment'],
        )

    class Meta:
        model = Task
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'