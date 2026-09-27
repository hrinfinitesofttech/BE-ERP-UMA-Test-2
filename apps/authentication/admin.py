from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('last_login', 'is_superuser', 'is_staff', 'is_active')
