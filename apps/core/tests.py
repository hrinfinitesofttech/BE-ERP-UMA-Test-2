from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from apps.authentication.models import User
from apps.core.models import CompanySetting, NumberingSetting
from apps.organization.models import Department, Role


class Phase1ApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth import get_user_model
        self.client.force_authenticate(user=get_user_model().objects.create_superuser(username="api_test_user", password="Test@12345"))
        call_command('seed_phase1')

    def test_company_api_camel_case(self):
        response = self.client.get('/api/company/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('companyName', data)
        self.assertIn('bankAccountNo', data)
        self.assertEqual(data['companyName'], 'Uma Techno Fab Private Limited')

    def test_departments_api(self):
        response = self.client.get('/api/departments/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 9)
        dept_codes = [d['code'] for d in data]
        self.assertIn('CRM', dept_codes)
        self.assertIn('PRD', dept_codes)

    def test_roles_api(self):
        response = self.client.get('/api/roles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 4)

    def test_employees_api(self):
        response = self.client.get('/api/employees/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 6)
        first_emp = data[0]
        self.assertIn('firstName', first_emp)
        self.assertIn('departmentName', first_emp)

    def test_auth_login_api(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'rajesh.admin',
            'password': 'admin123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('access', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['id'], 'EMP-001')

    def test_numbering_next_number_api(self):
        response = self.client.get('/api/numbering/next-number/?docType=lead')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['docType'], 'lead')
        self.assertEqual(data['nextNumber'], 'LEAD-2026-0105')


class SecurityHardeningTests(TestCase):
    """API must reject anonymous access and the destructive system endpoints must be locked."""

    def test_anonymous_api_access_is_rejected(self):
        client = APIClient()
        for url in ['/api/leads/', '/api/customers/', '/api/company/', '/api/sales-invoices/', '/api/employees/']:
            self.assertEqual(client.get(url).status_code, 401, url)

    def test_login_endpoint_is_public(self):
        res = APIClient().post('/api/auth/login/', {'username': 'nobody', 'password': 'bad'}, format='json')
        self.assertIn(res.status_code, (400, 401))

    def test_clear_all_data_disabled_and_deploy_needs_token(self):
        client = APIClient()
        res = client.post('/api/system/clear-all-data/', HTTP_X_DEPLOY_TOKEN='uma-erp-deploy-key-2026-secure-sync')
        self.assertEqual(res.status_code, 403)
        res = client.post('/api/system/deploy/', HTTP_X_DEPLOY_TOKEN='uma-erp-deploy-key-2026-secure-sync')
        self.assertEqual(res.status_code, 403)
