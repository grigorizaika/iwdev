from rest_framework import serializers

from .models import (Address, AddressOwner, CustomFile, FileOwner)
from clients.models import Client
from users.models import User as CustomUser



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


