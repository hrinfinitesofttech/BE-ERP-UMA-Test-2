from django.core.management.base import BaseCommand
from apps.core.models import CompanySetting, NumberingSetting
from apps.organization.models import Department, Role
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Seeds initial Company Settings, Numbering, Departments, Roles, and Employees for UMA ERP'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Phase 1 Data Seeding...'))

        # 1. Company Setting
        company, created = CompanySetting.objects.get_or_create(id=1)
        company.company_name = 'Uma Techno Fab Private Limited'
        company.tagline = 'Custom Heavy Fabrication & Make-to-Order Equipment Manufacturer'
        company.logo_url = '/logo.png'
        company.address = 'Plot No. 48/B, GIDC Industrial Estate, Makarpura'
        company.city = 'Vadodara'
        company.state = 'Gujarat'
        company.country = 'India'
        company.pincode = '390010'
        company.phone = '+91 265 2645800 / +91 98250 11223'
        company.email = 'info@umatechnofab.com'
        company.website = 'https://www.umatechnofab.com'
        company.gstin = '24AABCU9821R1ZX'
        company.pan = 'AABCU9821R'
        company.cin = 'U28112GJ2012PTC071234'
        company.financial_year = '2026-2027'
        company.currency = 'INR (₹)'
        company.timezone = 'Asia/Kolkata (IST)'
        company.bank_name = 'State Bank of India'
        company.bank_account_no = '30491827461'
        company.bank_ifsc = 'SBIN0001234'
        company.bank_branch = 'Industrial Estate Branch, Vadodara'
        company.save()
        self.stdout.write(self.style.SUCCESS('[OK] Company settings seeded.'))

        # 2. Numbering Settings
        numbering_data = [
            {'id': 'num-1', 'module': 'CRM', 'doc_type': 'lead', 'prefix': 'LEAD-2026-', 'current_number': 105, 'digit_count': 4, 'sample_preview': 'LEAD-2026-0106'},
            {'id': 'num-2', 'module': 'CRM', 'doc_type': 'enquiry', 'prefix': 'ENQ-2026-', 'current_number': 68, 'digit_count': 4, 'sample_preview': 'ENQ-2026-0069'},
            {'id': 'num-3', 'module': 'CRM', 'doc_type': 'opportunity', 'prefix': 'OPP-2026-', 'current_number': 54, 'digit_count': 4, 'sample_preview': 'OPP-2026-0055'},
            {'id': 'num-4', 'module': 'CRM', 'doc_type': 'quotation', 'prefix': 'QT-2026-', 'current_number': 132, 'digit_count': 4, 'sample_preview': 'QT-2026-0133'},
            {'id': 'num-5', 'module': 'CRM', 'doc_type': 'customer_po', 'prefix': 'CPO-2026-', 'current_number': 46, 'digit_count': 4, 'sample_preview': 'CPO-2026-0047'},
            {'id': 'num-6', 'module': 'CRM', 'doc_type': 'sales_order', 'prefix': 'SO-2026-', 'current_number': 49, 'digit_count': 4, 'sample_preview': 'SO-2026-0050'},
            {'id': 'num-7', 'module': 'Project', 'doc_type': 'project', 'prefix': 'PRJ-2026-', 'current_number': 49, 'digit_count': 4, 'sample_preview': 'PRJ-2026-0050'},
            {'id': 'num-8', 'module': 'Project', 'doc_type': 'job', 'prefix': 'JOB-2026-', 'current_number': 49, 'digit_count': 4, 'sample_preview': 'JOB-2026-0050'},
            {'id': 'num-9', 'module': 'CRM', 'doc_type': 'visit', 'prefix': 'VST-2026-', 'current_number': 38, 'digit_count': 4, 'sample_preview': 'VST-2026-0039'},
        ]
        for num in numbering_data:
            NumberingSetting.objects.update_or_create(id=num['id'], defaults=num)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(numbering_data)} Numbering series seeded.'))

        # 3. Departments
        dept_data = [
            {'id': 'dept-crm', 'code': 'CRM', 'name': 'CRM & Sales', 'manager_id': 'EMP-003', 'manager_name': 'Pravin Patel', 'description': 'Customer leads, enquiries, quotations and order acquisition', 'status': 'active', 'employee_count': 6},
            {'id': 'dept-prj', 'code': 'PRJ', 'name': 'Project Management', 'manager_id': 'EMP-001', 'manager_name': 'Rajesh Patel', 'description': 'Make-to-Order project schedules, milestones, delivery timelines', 'status': 'active', 'employee_count': 4},
            {'id': 'dept-des', 'code': 'DES', 'name': 'Design & Engineering', 'manager_id': 'EMP-005', 'manager_name': 'Dharmesh Joshi', 'description': '2D/3D CAD drawings, Engineering calculations, BOM revisions', 'status': 'active', 'employee_count': 5},
            {'id': 'dept-pur', 'code': 'PUR', 'name': 'Purchase & Procurement', 'manager_id': 'EMP-006', 'manager_name': 'Vikram Solanki', 'description': 'Raw material procurement, RFQs, vendor POs, supplier ledger', 'status': 'active', 'employee_count': 4},
            {'id': 'dept-str', 'code': 'STR', 'name': 'Store & Inventory', 'manager_id': 'EMP-008', 'manager_name': 'Hitesh Rawal', 'description': 'Raw material stock, GRN inward, bin locations, material issue slips', 'status': 'active', 'employee_count': 5},
            {'id': 'dept-prd', 'code': 'PRD', 'name': 'Production & Shop Floor', 'manager_id': 'EMP-004', 'manager_name': 'Bhavin Shah', 'description': 'Cutting, rolling, fabrication, welding, assembly, machine logs', 'status': 'active', 'employee_count': 22},
            {'id': 'dept-acc', 'code': 'ACC', 'name': 'Accounting & Finance', 'manager_id': 'EMP-003', 'manager_name': 'Pravin Patel', 'description': 'Customer/Vendor ledgers, tax invoices, GST, cashflow, P&L', 'status': 'active', 'employee_count': 4},
            {'id': 'dept-mnt', 'code': 'MNT', 'name': 'Maintenance & Service', 'manager_id': 'EMP-009', 'manager_name': 'Nilesh Vaghela', 'description': 'Factory machinery PM, breakdown repairs, site commissioning & AMC', 'status': 'active', 'employee_count': 5},
            {'id': 'dept-hr', 'code': 'HR', 'name': 'HR & Payroll', 'manager_id': 'EMP-010', 'manager_name': 'Sneha Dave', 'description': 'Recruitment, attendance, payroll calculations, safety training', 'status': 'active', 'employee_count': 3},
        ]
        dept_map = {}
        for dept in dept_data:
            obj, _ = Department.objects.update_or_create(id=dept['id'], defaults=dept)
            dept_map[dept['id']] = obj
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(dept_data)} Departments seeded.'))

        # 4. Roles
        roles_data = [
            {
                'id': 'role-superadmin',
                'name': 'Super Admin',
                'description': 'Owner & Managing Director with unconstrained system-wide privileges',
                'is_system': True,
                'permissions': [
                    {'module': 'CRM', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Project', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Designer', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Purchase', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Store', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Production', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Accounting', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Maintenance', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'HR', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Settings', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                ]
            },
            {
                'id': 'role-admin-family',
                'name': 'Admin (Family Member)',
                'description': 'Executive family member with portfolio-level cross-departmental access',
                'is_system': True,
                'permissions': [
                    {'module': 'CRM', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Project', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Production', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Purchase', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Store', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                ]
            },
            {
                'id': 'role-crm-manager',
                'name': 'CRM Manager',
                'description': 'Full CRM oversight, quotation approvals, customer master and sales pipeline management',
                'is_system': True,
                'permissions': [
                    {'module': 'CRM', 'page': 'All', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True, 'reject': True, 'assign': True, 'export': True, 'print': True},
                    {'module': 'Project', 'page': 'Job Master', 'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                ]
            },
            {
                'id': 'role-crm-employee',
                'name': 'CRM Employee / Sales Engineer',
                'description': 'Lead generation, follow-ups, customer visits, draft quotation preparation',
                'is_system': True,
                'permissions': [
                    {'module': 'CRM', 'page': 'Leads', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                    {'module': 'CRM', 'page': 'Enquiries', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                    {'module': 'CRM', 'page': 'Customers', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                    {'module': 'CRM', 'page': 'Quotations', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                    {'module': 'CRM', 'page': 'Follow-ups', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                    {'module': 'CRM', 'page': 'Visits', 'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False, 'reject': False, 'assign': False, 'export': True, 'print': True},
                ]
            },
        ]
        role_map = {}
        for role in roles_data:
            obj, _ = Role.objects.update_or_create(id=role['id'], defaults=role)
            role_map[role['id']] = obj
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(roles_data)} Roles seeded.'))

        # 5. Employees & Users
        emp_data = [
            {
                'id': 'EMP-000',
                'username': 'admin',
                'first_name': 'Super',
                'last_name': 'Admin',
                'email': 'admin@umatechnofab.com',
                'gender': 'male',
                'department_name': 'Project Management',
                'designation': 'System Administrator',
                'role_profile': role_map.get('role-superadmin'),
                'role_name': 'Super Admin',
                'employment_type': 'full_time',
                'status': 'active',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'id': 'EMP-001',
                'username': 'rajesh.admin',
                'first_name': 'Rajesh',
                'last_name': 'Patel',
                'email': 'rajesh@umatechnofab.com',
                'gender': 'male',
                'dob': '1974-05-12',
                'mobile': '+91 98250 11223',
                'phone': '+91 98250 11223',
                'address': 'B-14, Alkapuri Society, Vadodara, Gujarat',
                'department': dept_map.get('dept-prj'),
                'department_name': 'Project Management',
                'designation': 'Managing Director & Super Admin',
                'role_profile': role_map.get('role-superadmin'),
                'role_name': 'Super Admin',
                'joining_date': '2012-04-01',
                'employment_type': 'full_time',
                'status': 'active',
                'last_login_str': '2026-09-23 11:30 AM',
                'is_family_member': True,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'id': 'EMP-002',
                'username': 'ketan.admin',
                'first_name': 'Ketan',
                'last_name': 'Patel',
                'email': 'ketan@umatechnofab.com',
                'gender': 'male',
                'dob': '1978-08-20',
                'mobile': '+91 98250 33445',
                'phone': '+91 98250 33445',
                'address': 'Plot 22, Gotri Road, Vadodara, Gujarat',
                'department': dept_map.get('dept-prd'),
                'department_name': 'Production & Shop Floor',
                'designation': 'Executive Director (Operations)',
                'role_profile': role_map.get('role-admin-family'),
                'role_name': 'Admin (Family Member)',
                'reporting_manager_id': 'EMP-001',
                'reporting_manager_name': 'Rajesh Patel',
                'joining_date': '2012-04-01',
                'employment_type': 'full_time',
                'status': 'active',
                'last_login_str': '2026-09-23 10:15 AM',
                'is_family_member': True,
                'is_staff': True,
            },
            {
                'id': 'EMP-003',
                'username': 'pravin.crm',
                'first_name': 'Pravin',
                'last_name': 'Patel',
                'email': 'pravin@umatechnofab.com',
                'gender': 'male',
                'dob': '1982-11-15',
                'mobile': '+91 98250 55667',
                'phone': '+91 98250 55667',
                'address': 'Shreeji Bunglows, Vasna-Bhayli, Vadodara',
                'department': dept_map.get('dept-crm'),
                'department_name': 'CRM & Sales',
                'designation': 'Commercial Director & CRM Head',
                'role_profile': role_map.get('role-crm-manager'),
                'role_name': 'CRM Manager',
                'reporting_manager_id': 'EMP-001',
                'reporting_manager_name': 'Rajesh Patel',
                'joining_date': '2013-01-10',
                'employment_type': 'full_time',
                'status': 'active',
                'last_login_str': '2026-09-23 09:40 AM',
                'is_family_member': True,
                'is_staff': True,
            },
            {
                'id': 'EMP-004',
                'username': 'bhavin.prod',
                'first_name': 'Bhavin',
                'last_name': 'Shah',
                'email': 'bhavin.shah@umatechnofab.com',
                'gender': 'male',
                'dob': '1985-03-25',
                'mobile': '+91 98790 12345',
                'phone': '+91 98790 12345',
                'address': '402, Nilamber Heights, Manjalpur, Vadodara',
                'department': dept_map.get('dept-prd'),
                'department_name': 'Production & Shop Floor',
                'designation': 'Senior Production Manager',
                'role_profile': role_map.get('role-superadmin'),
                'role_name': 'Production Manager',
                'reporting_manager_id': 'EMP-002',
                'reporting_manager_name': 'Ketan Patel',
                'joining_date': '2015-06-15',
                'employment_type': 'full_time',
                'status': 'active',
                'last_login_str': '2026-09-23 08:30 AM',
                'is_family_member': False,
                'is_staff': True,
            },
            {
                'id': 'EMP-007',
                'username': 'amit.sales',
                'first_name': 'Amit',
                'last_name': 'Sharma',
                'email': 'amit.s@umatechnofab.com',
                'gender': 'male',
                'dob': '1992-07-14',
                'mobile': '+91 98790 55443',
                'phone': '+91 98790 55443',
                'address': '204, Fortune Complex, Sayajigunj, Vadodara',
                'department': dept_map.get('dept-crm'),
                'department_name': 'CRM & Sales',
                'designation': 'Senior Sales & Proposal Engineer',
                'role_profile': role_map.get('role-crm-employee'),
                'role_name': 'CRM Employee',
                'reporting_manager_id': 'EMP-003',
                'reporting_manager_name': 'Pravin Patel',
                'joining_date': '2019-09-01',
                'employment_type': 'full_time',
                'status': 'active',
                'last_login_str': '2026-09-23 11:10 AM',
                'is_family_member': False,
                'is_staff': False,
            },
        ]

        for item in emp_data:
            User.objects.filter(username=item['username']).exclude(id=item['id']).delete()
            user, _ = User.objects.update_or_create(
                id=item['id'],
                defaults={**item}
            )
            user.set_password('admin123')
            user.save()
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(emp_data)} Users/Employees seeded with default password: admin123.'))
        self.stdout.write(self.style.SUCCESS('Done: Phase 1 Seeding Complete!'))
