import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from apps.authentication.models import User
from apps.organization.models import Department

# 1. Update/Ensure 9 core departments
departments_data = [
    {'code': 'ACC', 'name': 'Accounting & Finance', 'description': 'Financial accounting, billing, GST, audits'},
    {'code': 'CRM', 'name': 'CRM & Sales', 'description': 'Client relations, inquiries, quotes, orders'},
    {'code': 'DES', 'name': 'Design & Engineering', 'description': 'CAD drawings, technical specs, engineering'},
    {'code': 'HR', 'name': 'HR & Payroll', 'description': 'Employee records, attendance, payroll'},
    {'code': 'MNT', 'name': 'Maintenance & Service', 'description': 'Machine servicing, plant maintenance'},
    {'code': 'PRD', 'name': 'Production & Shop Floor', 'description': 'Machining, assembly, shift tracking'},
    {'code': 'PRJ', 'name': 'Project Management', 'description': 'Milestones, project tracking, execution'},
    {'code': 'PUR', 'name': 'Purchase & Procurement', 'description': 'Vendor management, purchase orders, RFQs'},
    {'code': 'STR', 'name': 'Store & Inventory', 'description': 'Raw materials, stock management, issuing'},
]

print("--- SEEDING DEPARTMENTS ---")
for d in departments_data:
    dept, created = Department.objects.get_or_create(code=d['code'], defaults={'name': d['name'], 'description': d['description']})
    if not created and dept.name != d['name']:
        dept.name = d['name']
        dept.save()
    print(f"Department [{dept.code}]: {dept.name}")

# 2. Update all 6 users with real roles, scopes, and flags
user_configs = {
    'admin': {
        'role_type': 'super_admin',
        'role_name': 'Super Admin',
        'is_superuser': True,
        'is_staff': True,
        'is_family_member': False,
        'data_scope': 'all',
        'can_assign_tasks': True,
        'can_approve_leaves': True,
        'can_manage_attendance': True,
        'can_export_data': True,
        'assigned_modules': ['all'],
        'designation': 'System Administrator',
    },
    'rajesh.admin': {
        'role_type': 'super_admin',
        'role_name': 'Super Admin',
        'is_superuser': True,
        'is_staff': True,
        'is_family_member': True,
        'data_scope': 'all',
        'can_assign_tasks': True,
        'can_approve_leaves': True,
        'can_manage_attendance': True,
        'can_export_data': True,
        'assigned_modules': ['all'],
        'designation': 'Managing Director & Super Admin',
        'department_code': 'CRM',
    },
    'ketan.admin': {
        'role_type': 'admin',
        'role_name': 'Admin (Family Member)',
        'is_superuser': False,
        'is_staff': True,
        'is_family_member': True,
        'data_scope': 'all',
        'can_assign_tasks': True,
        'can_approve_leaves': True,
        'can_manage_attendance': True,
        'can_export_data': True,
        'assigned_modules': ['production', 'purchase', 'inventory', 'projects', 'quality', 'maintenance'],
        'designation': 'Executive Director (Operations)',
        'department_code': 'PRD',
    },
    'pravin.crm': {
        'role_type': 'department_manager',
        'role_name': 'Department Manager',
        'is_superuser': False,
        'is_staff': True,
        'is_family_member': True,
        'data_scope': 'department',
        'can_assign_tasks': True,
        'can_approve_leaves': True,
        'can_manage_attendance': True,
        'can_export_data': True,
        'assigned_modules': ['crm', 'sales', 'projects'],
        'designation': 'Commercial Director & CRM Head',
        'department_code': 'CRM',
    },
    'bhavin.prod': {
        'role_type': 'department_manager',
        'role_name': 'Department Manager',
        'is_superuser': False,
        'is_staff': True,
        'is_family_member': False,
        'data_scope': 'department',
        'can_assign_tasks': True,
        'can_approve_leaves': True,
        'can_manage_attendance': True,
        'can_export_data': True,
        'assigned_modules': ['production', 'inventory', 'quality', 'maintenance'],
        'designation': 'Senior Production Manager',
        'department_code': 'PRD',
    },
    'amit.sales': {
        'role_type': 'employee',
        'role_name': 'Staff',
        'is_superuser': False,
        'is_staff': False,
        'is_family_member': False,
        'data_scope': 'assigned',
        'can_assign_tasks': False,
        'can_approve_leaves': False,
        'can_manage_attendance': False,
        'can_export_data': False,
        'assigned_modules': ['crm', 'sales'],
        'designation': 'Senior Sales & Proposal Engineer',
        'department_code': 'CRM',
    },
}

print("\n--- UPDATING USERS ---")
for username, cfg in user_configs.items():
    u = User.objects.filter(username=username).first()
    if u:
        u.role_type = cfg['role_type']
        u.role_name = cfg['role_name']
        u.is_superuser = cfg['is_superuser']
        u.is_staff = cfg['is_staff']
        u.is_family_member = cfg['is_family_member']
        u.data_scope = cfg['data_scope']
        u.can_assign_tasks = cfg['can_assign_tasks']
        u.can_approve_leaves = cfg['can_approve_leaves']
        u.can_manage_attendance = cfg['can_manage_attendance']
        u.can_export_data = cfg['can_export_data']
        u.assigned_modules = cfg['assigned_modules']
        u.designation = cfg['designation']
        dept_code = cfg.get('department_code')
        if dept_code:
            dept = Department.objects.filter(code=dept_code).first()
            if dept:
                u.department = dept
                u.department_name = dept.name
        u.save()
        print(f"Updated {username}: role_type={u.role_type}, role_name={u.role_name}, data_scope={u.data_scope}")
    else:
        print(f"User {username} not found")

print("\nALL SEEDING COMPLETED SUCCESSFULLY!")
