from rest_framework import serializers

from .models import Client
from utils.serializers import AddressSerializer



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