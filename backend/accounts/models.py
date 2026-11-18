"""
GreenGrid Accounts Models.
Custom User model with email authentication and RBAC, plus Audit Log.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email address must be provided.')
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'customer')
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_ADMIN = 'admin'
    ROLE_CUSTOMER = 'customer'
    ROLE_FIELD_ENGINEER = 'field_engineer'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_CUSTOMER, 'Facility Customer'),
        (ROLE_FIELD_ENGINEER, 'Field Engineer'),
    ]

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150, blank=True, default='')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_CUSTOMER, db_index=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        db_table = 'users_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

class AuditLog(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'accounts_auditlog'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.user or 'System'}: {self.action} on {self.resource_type}"
