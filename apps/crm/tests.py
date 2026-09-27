from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from apps.crm.models import Lead, Customer, Quotation, CustomerPO, SalesOrder


class Phase2CrmApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command('seed_phase1')
        call_command('seed_phase2')

    def test_leads_list_and_camel_case(self):
        response = self.client.get('/api/leads/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 4)
        first_lead = data[0]
        self.assertIn('leadNo', first_lead)
        self.assertIn('companyName', first_lead)
        self.assertIn('productName', first_lead)

    def test_create_new_lead_auto_numbering(self):
        response = self.client.post('/api/leads/', {
            'companyName': 'Adani Ports & Special Economic Zone',
            'contactPerson': 'Mr. Adani',
            'mobile': '+91 98980 12345',
            'productName': 'Heavy Marine Storage Tank',
            'quantity': 1,
            'budget': 7500000,
            'priority': 'high',
            'source': 'referral',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['leadNo'].startswith('LEAD-2026-'))
        self.assertEqual(data['companyName'], 'Adani Ports & Special Economic Zone')

    def test_convert_lead_to_customer(self):
        lead = Lead.objects.filter(status='requirement_received').first() or Lead.objects.first()
        response = self.client.post(f'/api/leads/{lead.id}/convert/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('customer', data)
        self.assertIn('enquiry', data)
        self.assertIn('opportunity', data)
        # Check DB updated
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'won')
        self.assertIsNotNone(lead.converted_customer_id)

    def test_customers_list(self):
        response = self.client.get('/api/customers/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 4)
        first_cust = data[0]
        self.assertIn('customerCode', first_cust)
        self.assertIn('companyName', first_cust)

    def test_quotation_revision_and_details(self):
        response = self.client.get('/api/quotations/QT-2026-0118/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['quotationNumber'], 'QT-2026-0118')
        self.assertIn('revisions', data)
        self.assertTrue(len(data['revisions']) >= 2)

    def test_convert_cpo_to_sales_order(self):
        po = CustomerPO.objects.first()
        response = self.client.post(f'/api/customer-pos/{po.id}/convert-to-so/')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['salesOrderNumber'].startswith('SO-2026-'))
        self.assertEqual(data['customerName'], po.customer_name)
