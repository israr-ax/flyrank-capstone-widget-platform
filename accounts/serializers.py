from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from .models import Tenant, TenantMembership


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_name = serializers.CharField(max_length=255)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken.')
        return value

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                password=validated_data['password'],
            )
            tenant = Tenant.objects.create(name=validated_data['tenant_name'])
            TenantMembership.objects.create(user=user, tenant=tenant, role=TenantMembership.ROLE_OWNER)
        return user