# users/serializers.py
from rest_framework import serializers
from .models import User, Address

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'clerk_id', 'username', 'email', 'first_name', 'last_name', 'phone', 'avatar']
        read_only_fields = ['clerk_id']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']