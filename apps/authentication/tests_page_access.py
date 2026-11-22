from django.test import TestCase

from apps.authentication.models import User
from apps.organization.models import Department


class PageLevelAccessPersistenceTests(TestCase):
    def setUp(self):
        self.a = Department.objects.create(
            id='d-a', code='A', name='Dept A', assigned_modules=['crm'],
            default_permissions={'crm': ['view']}, status='active',
        )
        self.b = Department.objects.create(
            id='d-b', code='B', name='Dept B', assigned_modules=['store'],
            default_permissions={'store': ['view']}, status='active',
        )

    def _user(self, uid, **kw):
        return User.objects.create(
            id=uid, username=uid.lower(), first_name='T', last_name='U',
            department=self.a, department_name='Dept A', **kw,
        )

    def test_department_change_keeps_page_level_access(self):
        pages = {'crm.leads': ['view', 'create'], 'store.grn': ['view']}
        u = self._user('EMP-P1', assigned_modules=['crm', 'store'],
                       custom_permissions={'crm': ['view', 'create'], 'store': ['view'], 'pages': pages})
        u.department = self.b
        u.department_name = 'Dept B'
        u.save()
        u.refresh_from_db()
        self.assertEqual(u.custom_permissions['pages'], pages)
        self.assertEqual(u.assigned_modules, ['crm', 'store'])
        self.assertTrue(u.permissions_review_required)

    def test_legacy_employee_still_resets_on_department_change(self):
        u = self._user('EMP-L1', assigned_modules=['crm'], custom_permissions={'crm': ['view', 'edit']})
        u.department = self.b
        u.department_name = 'Dept B'
        u.save()
        u.refresh_from_db()
        self.assertEqual(u.assigned_modules, ['store'])
        self.assertEqual(u.custom_permissions, {'store': ['view']})
