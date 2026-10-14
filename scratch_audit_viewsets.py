import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from erp_backend.urls import api_router

print("=== AUDIT OF ALL API ROUTER VIEWSETS AND PERMISSIONS ===")
for prefix, viewset, basename in api_router.registry:
    perms = getattr(viewset, 'permission_classes', [])
    perm_names = [p.__name__ if hasattr(p, '__name__') else str(p) for p in perms]
    print(f"/{prefix:30} -> {viewset.__name__:35} | Permissions: {perm_names}")
