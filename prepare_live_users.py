import sqlite3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from django.contrib.auth.hashers import make_password

conn = sqlite3.connect('live_pa_db.sqlite3')
cur = conn.cursor()

# Set standard password hash for Admin@123456
pwd_hash = make_password('Admin@123456')

cur.execute("PRAGMA table_info(authentication_user)")
columns = [c[1] for c in cur.fetchall()]

cur.execute("SELECT * FROM authentication_user WHERE id = 'EMP-000' OR id = 'EMP-001' LIMIT 1")
sample_row = dict(zip(columns, cur.fetchone()))

def insert_or_update_user(user_dict):
    row_data = sample_row.copy()
    row_data.update(user_dict)
    
    cur.execute("SELECT id FROM authentication_user WHERE username = ? OR id = ?", [row_data['username'], row_data['id']])
    res = cur.fetchone()
    if res:
        # update
        set_clauses = ", ".join([f"{k} = ?" for k in user_dict.keys()])
        cur.execute(f"UPDATE authentication_user SET {set_clauses} WHERE id = ?", list(user_dict.values()) + [res[0]])
        print(f"Updated user: {row_data['username']} ({res[0]})")
    else:
        # insert
        cols_str = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])
        vals = [row_data.get(c, '') for c in columns]
        cur.execute(f"INSERT INTO authentication_user ({cols_str}) VALUES ({placeholders})", vals)
        print(f"Inserted user: {row_data['username']} ({row_data['id']})")

# 1. Update Durgesh Jadav to have Admin@123456
insert_or_update_user({
    'id': 'EMP-001',
    'username': 'durgesh.jadav',
    'email': 'jadavdurgesh2020@gmail.com',
    'first_name': 'Durgesh',
    'last_name': 'Jadav',
    'password': pwd_hash,
    'role_type': 'super_admin',
    'role_name': 'Managing Director & Super Admin',
    'designation': 'Managing Director & Super Admin',
    'department_name': 'CRM & Sales',
    'department_id': 'dept-crm',
    'data_scope': 'all',
    'is_superuser': 1,
    'is_staff': 1,
    'is_active': 1,
    'is_family_member': 1,
})

# 2. Update Hardik Daki to have Admin@123456
insert_or_update_user({
    'id': 'EMP-000',
    'username': 'hardik.daki',
    'email': 'admin@umatechnofab.com',
    'first_name': 'Super Admin',
    'last_name': 'Hardik',
    'password': pwd_hash,
    'role_type': 'super_admin',
    'role_name': 'Super Admin',
    'designation': 'System Administrator',
    'department_name': 'Accounting & Finance',
    'department_id': 'dept-acc',
    'data_scope': 'all',
    'is_superuser': 1,
    'is_staff': 1,
    'is_active': 1,
    'is_family_member': 1,
})

# 3. Update Deepbhai Manvar
insert_or_update_user({
    'id': '002',
    'username': 'Deepmanvar',
    'email': 'deepmanvar@gmail.com',
    'first_name': 'Deepbhai',
    'last_name': 'Manvar',
    'password': pwd_hash,
    'role_type': 'admin',
    'role_name': 'Admin (Family Member)',
    'designation': 'CRM & Sales',
    'department_name': 'CRM & Sales',
    'department_id': 'dept-crm',
    'data_scope': 'own',
    'is_superuser': 0,
    'is_staff': 1,
    'is_active': 1,
    'is_family_member': 1,
})

# 4. Update hemant bhai
insert_or_update_user({
    'id': '003',
    'username': 'hemantbhai',
    'email': 'hemant@gmail.com',
    'first_name': 'hemant',
    'last_name': 'bhai',
    'password': pwd_hash,
    'role_type': 'admin',
    'role_name': 'Admin (Family Member)',
    'designation': 'Purchase & Procurement',
    'department_name': 'Purchase Management',
    'department_id': 'dept-pur',
    'data_scope': 'own',
    'is_superuser': 0,
    'is_staff': 1,
    'is_active': 1,
    'is_family_member': 1,
})

# 5. Add / Update Kuldeep PATEL (from Screenshot 2)
insert_or_update_user({
    'id': 'EMP-003',
    'username': 'kuldeep.patel',
    'email': 'patel@gmail.com',
    'first_name': 'Kuldeep',
    'last_name': 'PATEL',
    'password': pwd_hash,
    'role_type': 'admin',
    'role_name': 'Admin (Family Member)',
    'designation': 'Sales Executive',
    'department_name': 'Accounting & Finance',
    'department_id': 'dept-acc',
    'data_scope': 'own',
    'mobile': '7600512333',
    'phone': '7600512333',
    'is_superuser': 0,
    'is_staff': 1,
    'is_active': 1,
    'is_family_member': 1,
})

# 6. Add admin account for fallback / tests
insert_or_update_user({
    'id': 'EMP-ADM',
    'username': 'admin',
    'email': 'sysadmin@umatechnofab.com',
    'first_name': 'Enterprise',
    'last_name': 'Admin',
    'password': pwd_hash,
    'role_type': 'super_admin',
    'role_name': 'Super Admin',
    'designation': 'System Administrator',
    'department_name': 'Management',
    'department_id': 'dept-mgt',
    'data_scope': 'all',
    'is_superuser': 1,
    'is_staff': 1,
    'is_active': 1,
    'is_family_member': 1,
})

conn.commit()

# Print all users in database
cur.execute("SELECT id, username, first_name, last_name, email, role_name, data_scope, is_active FROM authentication_user ORDER BY id")
print("\n=== VERIFIED USERS IN LIVE DB ===")
for r in cur.fetchall():
    print(r)

conn.close()
