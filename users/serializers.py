import datetime

from rest_framework import serializers

from .models import Absence, Company, Role, User as CustomUser
from utils.serializers import AddressSerializer


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
        depth = 1


# For user registration only
class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, )

    def __init__(self, *args, **kwargs):
        self.create_cognito_user_on_post = kwargs.pop(
            'create_cognito_user', True)
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

        role = validated_data.get('role', 'Worker')
        user.role, _ = Role.objects.get_or_create(name=role)
        user.save()

        return user

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'surname', 'phone', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }
        depth = 1


# For user display and modification only
class UserSerializer(serializers.ModelSerializer):
    addresses = serializers.SerializerMethodField()
    address_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    file_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        source='company', queryset=Company.objects.all())
    supervisor = SupervisorSerializer(read_only=True)
    supervisor_id = serializers.PrimaryKeyRelatedField(
        source='supervisor',  queryset=CustomUser.objects.all())
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source='role', queryset=Role.objects.all())

    def get_addresses(self, obj):
        queryset = obj.addresses()
        if len(queryset) == 0:
            return None
        serializer = AddressSerializer(queryset, many=True)
        return serializer.data


    class Meta:
        model = CustomUser
        exclude = ('password', 'last_login', 'is_staff',
                   'is_superuser', 'groups', 'user_permissions')
        depth = 1


class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class AbsenceSerializer(serializers.ModelSerializer):
    total_days = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user', queryset=CustomUser.objects.all())

    def get_total_days(self, obj):
        return obj.total_days()

    def validate(self, data):
        try:
            initial_data = dict(self.to_representation(self.instance))
        except AttributeError:
            # TODO: can this generate bugs?
            pass

        if (('date_start' in data and 'date_end' in data)
                and (data['date_start'] > data['date_end'])):
            raise serializers.ValidationError(
                'date_end must be later than date_start')

        elif 'date_start' in data and 'date_end' not in data:
            date_end = datetime.datetime.strptime(
                initial_data['date_end'], "%Y-%m-%d").date()
            if data['date_start'] > date_end:
                raise serializers.ValidationError(
                    'date_end must be later than date_start')

        elif 'date_start' not in data and 'date_end' in data:
            date_start = datetime.datetime.strptime(
                initial_data['date_start'], "%Y-%m-%d").date()
            if data['date_end'] < date_start:
                raise serializers.ValidationError(
                    'date_end must be later than date_start')

        elif 'date_start' not in data and 'date_end' in data:
            date_start = datetime.datetime.strptime(
                initial_data['date_start'], "%Y-%m-%d").date()

        return super(AbsenceSerializer, self).validate(data)

    class Meta:
        model = Absence
        fields = '__all__'
