"""
GreenGrid Accounts Serializers.
"""

from rest_framework import serializers
from accounts.models import CustomUser, AuditLog

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    assigned_facility_ids = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'is_active', 'date_joined', 'assigned_facility_ids'
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'assigned_facility_ids']

    def get_assigned_facility_ids(self, obj):
        if hasattr(obj, 'facility_assignments'):
            return list(obj.facility_assignments.values_list('facility_id', flat=True))
        return []

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'role', 'phone', 'is_active'
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        clean = value.strip().lower()
        if CustomUser.objects.filter(email=clean).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return clean

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'action', 'resource_type',
            'resource_id', 'ip_address', 'timestamp', 'details'
        ]
        read_only_fields = fields
