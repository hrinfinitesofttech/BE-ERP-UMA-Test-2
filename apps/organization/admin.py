from django.contrib import admin
from .models import Department, Role

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'manager_id', 'manager_name', 'status')
    search_fields = ('id', 'code', 'name', 'manager_id')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_system', 'department_id', 'created_at', 'updated_at')
    search_fields = ('id', 'name', 'department_id')
    list_filter = ('is_system', 'created_at', 'updated_at')
