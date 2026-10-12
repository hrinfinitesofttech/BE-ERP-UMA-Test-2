import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from apps.organization.models import Department
from apps.authentication.models import User

ALL_MODULES = [
    'crm', 'projects', 'purchase', 'store', 'production', 
    'accounting', 'hr', 'maintenance', 'designer', 'nesting', 
    'qc', 'dispatch', 'documents'
]

STANDARD_DEPARTMENTS = [
    {
        'code': 'CRM',
        'name': 'CRM & Sales',
        'description': 'Customer relationships, inquiries, quotations, and sales order processing.',
        'modules': ['crm'],
        'default_permissions': {
            'crm': {'leads': ['view', 'create', 'edit'], 'quotations': ['view', 'create'], 'sales_orders': ['view']}
        }
    },
    {
        'code': 'PRJ',
        'name': 'Project Management',
        'description': 'MTO Project job planning, 16-stage tracking, and task allocations.',
        'modules': ['projects'],
        'default_permissions': {
            'projects': {'jobs': ['view', 'create', 'edit'], 'tasks': ['view', 'create', 'edit', 'assign']}
        }
    },
    {
        'code': 'DES',
        'name': 'Designer & Engineering',
        'description': 'CAD/CAM drawings, GA drawings, BOM finalization, and revisions.',
        'modules': ['designer', 'documents'],
        'default_permissions': {
            'designer': {'drawings': ['view', 'create', 'edit'], 'bom': ['view', 'create', 'edit']}
        }
    },
    {
        'code': 'NST',
        'name': 'Nesting Programming',
        'description': 'CNC plate cutting nesting, plate layout optimization, and offcut tracking.',
        'modules': ['nesting', 'production'],
        'default_permissions': {
            'nesting': {'nesting_plans': ['view', 'create', 'edit']}
        }
    },
    {
        'code': 'PUR',
        'name': 'Purchase Management',
        'description': 'Vendor quotations, purchase requisitions, PO creation, and tracking.',
        'modules': ['purchase'],
        'default_permissions': {
            'purchase': {'purchase_orders': ['view', 'create', 'edit'], 'requisitions': ['view', 'create']}
        }
    },
    {
        'code': 'STR',
        'name': 'Store & Inventory',
        'description': 'Raw material stock, GRN inspection inwarding, issue slips, and bin management.',
        'modules': ['store'],
        'default_permissions': {
            'store': {'stock': ['view', 'create', 'edit'], 'grn': ['view', 'create'], 'issue': ['view', 'create']}
        }
    },
    {
        'code': 'PRD',
        'name': 'Production & Manufacturing',
        'description': 'Work order operations, shop floor WIP tracking, shift entry, and machinery.',
        'modules': ['production'],
        'default_permissions': {
            'production': {'work_orders': ['view', 'edit'], 'shift_entry': ['view', 'create', 'edit'], 'wip': ['view']}
        }
    },
    {
        'code': 'QC',
        'name': 'Quality Control',
        'description': 'NDT inspection, radiography, hydro testing, and QC clearance handover.',
        'modules': ['qc', 'production'],
        'default_permissions': {
            'qc': {'inspection': ['view', 'create', 'edit', 'approve']}
        }
    },
    {
        'code': 'DSP',
        'name': 'Dispatch & Packing',
        'description': 'Finished equipment packaging, transit insurance, and delivery challans.',
        'modules': ['dispatch', 'production'],
        'default_permissions': {
            'dispatch': {'delivery_challans': ['view', 'create', 'edit', 'print']}
        }
    },
    {
        'code': 'ACC',
        'name': 'Accounting & Finance',
        'description': 'Invoicing, ledger accounts, payment collections, and financial reports.',
        'modules': ['accounting'],
        'default_permissions': {
            'accounting': {'invoices': ['view', 'create', 'edit'], 'payments': ['view', 'create']}
        }
    },
    {
        'code': 'HR',
        'name': 'HR & Payroll',
        'description': 'Staff directory, attendance records, leave approvals, shifts, and payroll.',
        'modules': ['hr'],
        'default_permissions': {
            'hr': {'attendance': ['view', 'create'], 'leaves': ['view', 'create'], 'payroll': ['view']}
        }
    },
    {
        'code': 'MNT',
        'name': 'Maintenance & Services',
        'description': 'Machinery breakdown logs, preventive maintenance schedule, and equipment spares.',
        'modules': ['maintenance'],
        'default_permissions': {
            'maintenance': {'breakdown': ['view', 'create', 'edit'], 'schedule': ['view', 'edit']}
        }
    },
    {
        'code': 'DOC',
        'name': 'Documents Management',
        'description': 'Mill test certificates (MTC), client drawings, inspection dossiers, and compliance.',
        'modules': ['documents'],
        'default_permissions': {
            'documents': {'files': ['view', 'create', 'edit', 'export']}
        }
    },
]

for d_info in STANDARD_DEPARTMENTS:
    dept, created = Department.objects.get_or_create(
        code=d_info['code'],
        defaults={
            'id': f"dept-{d_info['code'].lower()}",
            'name': d_info['name'],
            'description': d_info['description'],
            'assigned_modules': d_info['modules'],
            'default_permissions': d_info['default_permissions'],
            'status': 'active',
            'created_by': 'Super Admin'
        }
    )
    if not created:
        dept.name = d_info['name']
        dept.description = d_info['description']
        dept.assigned_modules = d_info['modules']
        dept.default_permissions = d_info['default_permissions']
        dept.status = 'active'
        dept.save()
    print(f"[{'CREATED' if created else 'UPDATED'}] {dept.code} - {dept.name} (modules: {dept.assigned_modules})")

# Ensure Super Admin has super_admin role and all modules
admin_users = User.objects.filter(is_superuser=True)
for au in admin_users:
    au.role_type = 'super_admin'
    au.data_scope = 'all'
    au.assigned_modules = ALL_MODULES
    au.can_assign_tasks = True
    au.can_approve_leaves = True
    au.can_manage_attendance = True
    au.can_export_data = True
    au.save()
    print(f"Configured Super Admin: {au.username} ({au.name})")

print("Department and RBAC setup completed successfully!")
