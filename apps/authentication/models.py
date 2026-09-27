from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.CharField(max_length=64, primary_key=True)
    gender = models.CharField(max_length=20, default='male')
    dob = models.CharField(max_length=30, blank=True, default='')
    mobile = models.CharField(max_length=30, blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    address = models.TextField(blank=True, default='')
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    department_name = models.CharField(max_length=100, blank=True, default='')
    designation = models.CharField(max_length=100, blank=True, default='')
    role_profile = models.ForeignKey(
        'organization.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    role_name = models.CharField(max_length=100, blank=True, default='')
    reporting_manager_id = models.CharField(max_length=64, blank=True, null=True)
    reporting_manager_name = models.CharField(max_length=150, blank=True, null=True)
    joining_date = models.CharField(max_length=30, blank=True, default='')
    employment_type = models.CharField(max_length=50, default='full_time')
    status = models.CharField(max_length=30, default='active')
    last_login_str = models.CharField(max_length=60, blank=True, default='')
    is_family_member = models.BooleanField(default=False)
    profile_photo = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id})"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}".strip()
