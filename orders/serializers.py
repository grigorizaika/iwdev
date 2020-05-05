from rest_framework import serializers

from .models import Order, Task
from clients.models import Client
from clients.serializers import ClientSerializer
from users.models import User as CustomUser
from users.serializers import UserSerializer
from utils.models import Address
from utils.serializers import AddressSerializer

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
        print('in validated_data: ', validated_data)
        return Order.objects.create(
            name = validated_data['name'],
            client = validated_data['client'],
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
    order = OrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(
                    source='order',
                    queryset=Order.objects.all())

    worker = UserSerializer(read_only=True)
    worker_id = serializers.PrimaryKeyRelatedField(
                    source='worker',
                    queryset=CustomUser.objects.all())

    worker_substitution = UserSerializer(read_only=True)
    worker_substitution_id = serializers.PrimaryKeyRelatedField(
                    source='worker_substitution',
                    queryset=CustomUser.objects.all(),
                    required=False)

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


