from django.db import models
import uuid


class Department(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    manager_id = models.CharField(max_length=64, blank=True, null=True)
    manager_name = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, default='active')
    employee_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"dept-{self.code.lower()}"
        super().save(*args, **kwargs)


class Role(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    is_system = models.BooleanField(default=False)
    department_id = models.CharField(max_length=64, blank=True, null=True)
    permissions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"role-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
