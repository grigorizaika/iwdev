from rest_framework import serializers

from clients.models import Client
from orders.models import (Order, Task)
from users.models import User as CustomUser
from users.models import (Company, Role)
from utils.models import (Address, AddressOwner, CustomFile, FileOwner)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class SupervisorSerializer(serializers.ModelSerializer):
    address_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    file_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = CustomUser
        exclude = ('password', 'last_login', 'is_staff', 
                    'is_superuser', 'groups', 'user_permissions', 
                    'supervisor')
        depth=1

class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, )

    def __init__(self, *args, **kwargs):
        self.create_cognito_user_on_post = kwargs.pop('create_cognito_user', True)
        super(RegistrationSerializer, self).__init__(*args, **kwargs)

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
            password=password,
            create_cognito_user=self.create_cognito_user_on_post
        )
        try:
            user.role = Role.objects.get(name=validated_data.get('role'))
        except Role.DoesNotExist:
            print('role ', validated_data.get('role'), ' does not exist')
        user.save()

        return user


    def update(self, instance, validated_data):
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
        depth=1


# TODO: I have both UserSerializer AND RegistrationSerilizer, pick one
class UserSerializer(serializers.ModelSerializer):
    addresses = serializers.SerializerMethodField()
    address_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    file_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    #role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    #supervisor = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    #company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(source='company',  queryset=Company.objects.all(), )

    supervisor = SupervisorSerializer(read_only=True)
    supervisor_id = serializers.PrimaryKeyRelatedField(source='supervisor',  queryset=CustomUser.objects.all(), )

    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(source='role',  queryset=Role.objects.all(), )


    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            phone=validated_data['phone'],
            password=validated_data['password'],
        )
        user.role = validated_data['role_id']
        return user


    def get_addresses(self, obj):
        queryset = obj.addresses()
        print('QUERYSET', queryset)
        if len(queryset) == 0:
            return None
        serializer = AddressSerializer(queryset, many=True)
        return serializer.data


    class Meta:
        model = CustomUser
        exclude = ('password', 'last_login', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        depth=1


class AddressOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressOwner
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    owner_email = serializers.SerializerMethodField()
    owner_class = serializers.SerializerMethodField()
    owner = serializers.PrimaryKeyRelatedField(queryset=AddressOwner.objects.all())

    def get_owner_class(self, obj):
        # TODO: surround with try-except
        return obj.get_owner_instance().__class__.__name__


    def get_owner_email(self, obj):
        # TODO: surround with try-except
        owner_instance = obj.get_owner_instance()
        if(isinstance(owner_instance, CustomUser) or isinstance(owner_instance, Client)):
            return owner_instance.email
        else:
            return 'Only Users and Clients have emails'


    class Meta:
        model = Address
        #fields = '__all__'
        fields = [
            'id', 'street', 'house_no', 'flat_no', 'city', 'district', 
            'country', 'postal_code', 'owner', 'owner_email', 'owner_class'
        ]
        depth=1


class ClientSerializer(serializers.ModelSerializer):
    address_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    file_owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Client
        fields = '__all__'
        depth=1

    addresses = serializers.SerializerMethodField()

    def get_addresses(self, obj):
        queryset = obj.addresses()
        if len(queryset) == 0:
            return None
        serializer = AddressSerializer(queryset, many=True)
        return serializer.data

    def create(self, validated_data):
        return Client.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            contact_name=validated_data['contact_name'],
            contact_phone=validated_data['contact_phone']
        )


class OrderSerializer(serializers.ModelSerializer):
    #address = serializers.StringRelatedField()
    #client_name = serializers.SerializerMethodField()
    #client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    #address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())

    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(source='client',  queryset=Client.objects.all(), )

    address = AddressSerializer(read_only=True)
    address_id = serializers.PrimaryKeyRelatedField(source='address',  queryset=Address.objects.all(), )

    def create(self, validated_data):
        return Order.objects.create(
            name = validated_data['name'],
            client = validated_data['client_id'],
            billing_period = validated_data['billing_period'],
            description = validated_data['description'],
            address = validated_data['address']
        )

    def get_client_name(self, obj):
        return obj.client.name

    class Meta:
        model = Order
        fields = '__all__'
        depth=1


class TaskSerializer(serializers.ModelSerializer):
    #order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    # TODO: May need to restrict this to users only (workers?)
    #worker = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    order = OrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(source='order',  queryset=Order.objects.all(), )

    worker = UserSerializer(read_only=True)
    worker_id = serializers.PrimaryKeyRelatedField(source='worker',  queryset=CustomUser.objects.all(), )

    worker_substitution  = UserSerializer(read_only=True)
    worker_substitution_id = serializers.PrimaryKeyRelatedField(source='worker_substitution',  queryset=CustomUser.objects.all(), )

    def create(self, validated_data):
        print('validated_data:', validated_data)
        return Task.objects.create(
            order=validated_data['order'],
            name=validated_data['name'],
            date=validated_data['date'],
            manual_time_set=validated_data['manual_time_set'],
            worker=validated_data['worker'],
            description=validated_data['description'],
            comment=validated_data['comment'],
        )

    class Meta:
        model = Task
        fields = '__all__'
        depth=1




class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class FileSerializer(serializers.ModelSerializer):
    owner_instance_id = serializers.SerializerMethodField()
    owner_instance_class = serializers.SerializerMethodField()
    owner = serializers.PrimaryKeyRelatedField(queryset=FileOwner.objects.all())

    def get_owner_instance_class(self, obj):
        # TODO: surround with try-except
        return obj.get_owner_instance().__class__.__name__

    def get_owner_instance_id(self, obj):
        # TODO: surround with try-except
        return obj.get_owner_instance().id

    class Meta:
        model = CustomFile
        fields = [
            'id', 'name', 'location', 'owner', 
            'owner_instance_class', 'owner_instance_id',
        ]
        depth=1



class FileOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileOwner
        fields = '__all__'