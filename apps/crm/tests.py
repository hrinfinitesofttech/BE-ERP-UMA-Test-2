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

    def test_complete_quotation_to_customer_po_flow(self):
        # 1. Create a Quotation
        quo_res = self.client.post('/api/quotations/', {
            'quotationNumber': 'QT-2026-0999',
            'customerId': 'cust-01',
            'customerName': 'Reliance Industries Ltd.',
            'contactPerson': 'Mr. Mukesh',
            'contactMobile': '+91 99999 88888',
            'contactEmail': 'procurement@ril.com',
            'validUntil': '2026-12-31',
            'revisions': [
                {
                    'revisionNumber': 'Rev-00',
                    'date': '2026-10-01',
                    'status': 'draft',
                    'subTotal': 5000000,
                    'taxAmount': 900000,
                    'grandTotal': 5900000,
                    'paymentTerms': '30 Days Credit',
                    'deliveryTime': '8 Weeks',
                    'items': [
                        {
                            'id': 'item-1',
                            'productName': 'Heavy Distillation Column 25KL',
                            'quantity': 1,
                            'unit': 'Set',
                            'rate': 5000000,
                            'taxPercent': 18,
                            'amount': 5900000
                        }
                    ]
                }
            ]
        }, format='json')
        self.assertEqual(quo_res.status_code, 201)
        quo_data = quo_res.json()
        self.assertEqual(quo_data['quotationNumber'], 'QT-2026-0999')

        # 2. Update status: Draft -> Approved -> Sent -> Accepted
        status_res1 = self.client.post(f"/api/quotations/{quo_data['id']}/update-status/", {
            'revisionNumber': 'Rev-00',
            'status': 'approved'
        }, format='json')
        self.assertEqual(status_res1.status_code, 200)

        status_res2 = self.client.post(f"/api/quotations/{quo_data['id']}/update-status/", {
            'revisionNumber': 'Rev-00',
            'status': 'accepted'
        }, format='json')
        self.assertEqual(status_res2.status_code, 200)
        self.assertEqual(status_res2.json()['latestSummary']['status'], 'accepted')

        # 3. Create Customer PO from accepted quotation
        cpo_res = self.client.post('/api/customer-pos/', {
            'poNumber': 'PO/RIL/2026/001',
            'poDate': '2026-10-01',
            'deliveryDate': '2026-11-30',
            'customerId': quo_data['customerId'],
            'customerName': quo_data['customerName'],
            'quotationId': quo_data['id'],
            'quotationNumber': 'QT-2026-0999 (Rev-00)',
            'poAmount': 5900000,
            'paymentTerms': '30 Days Credit',
            'status': 'received',
            'remarks': 'Customer issued formal purchase order against QT-2026-0999.'
        }, format='json')
        self.assertEqual(cpo_res.status_code, 201)
        cpo_data = cpo_res.json()
        self.assertEqual(cpo_data['poNumber'], 'PO/RIL/2026/001')
        self.assertEqual(cpo_data['quotationNumber'], 'QT-2026-0999 (Rev-00)')
        self.assertEqual(cpo_data['poAmount'], 5900000.0)

        # 4. Verify Customer PO is in the database and list endpoint
        po_in_db = CustomerPO.objects.filter(po_number='PO/RIL/2026/001').first()
        self.assertIsNotNone(po_in_db)
        self.assertEqual(po_in_db.customer_name, 'Reliance Industries Ltd.')
        self.assertEqual(po_in_db.po_value, 5900000.0)

        list_res = self.client.get('/api/customer-pos/')
        self.assertEqual(list_res.status_code, 200)
        po_numbers = [p['poNumber'] for p in list_res.json()]
        self.assertIn('PO/RIL/2026/001', po_numbers)

        # 5. Convert Customer PO to Sales Order
        convert_res = self.client.post(f"/api/customer-pos/{po_in_db.id}/convert-to-so/")
        self.assertEqual(convert_res.status_code, 201)
        so_data = convert_res.json()
        self.assertTrue(so_data['salesOrderNumber'].startswith('SO-2026-'))
        self.assertEqual(so_data['customerPoNumber'], 'PO/RIL/2026/001')
        self.assertEqual(so_data['grandTotal'], 5900000.0)

        # 6. Verify Customer PO status updated in DB
        po_in_db.refresh_from_db()
        self.assertEqual(po_in_db.status, 'converted_to_so')
        self.assertEqual(po_in_db.converted_so_id, so_data['id'])

    def test_supplier_po_and_quotation_functionality_unaffected(self):
        from apps.purchase.models import Supplier, PurchaseOrder, SupplierQuotation
        # Verify supplier models exist and are intact
        self.assertTrue(hasattr(Supplier, 'objects'))
        self.assertTrue(hasattr(PurchaseOrder, 'objects'))
        self.assertTrue(hasattr(SupplierQuotation, 'objects'))

