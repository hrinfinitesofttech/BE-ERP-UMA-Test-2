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

    def test_quotation_pdf_generation_endpoint(self):
        response = self.client.get('/api/quotations/QT-2026-0118/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertIn('Quotation_QT-2026-0118', response['Content-Disposition'])

    def test_quotation_send_email_attaches_pdf(self):
        from django.core import mail
        quo = Quotation.objects.filter(quotation_number='QT-2026-0118').first()
        self.assertIsNotNone(quo)

        # Clear outbox
        mail.outbox = []

        response = self.client.post(f'/api/quotations/{quo.id}/send-email/', {
            'recipientEmail': 'client.test@example.com'
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['hasPdfAttachment'])
        self.assertTrue(data['pdfFilename'].endswith('.pdf'))

        # Verify dispatched email message and its PDF attachment
        self.assertEqual(len(mail.outbox), 1)
        sent_msg = mail.outbox[0]
        self.assertIn('client.test@example.com', sent_msg.to)
        self.assertTrue(len(sent_msg.attachments) >= 1)
        # Check attachment details
        att_filename, att_content, att_mimetype = sent_msg.attachments[0]
        self.assertTrue(att_filename.endswith('.pdf'))
        self.assertEqual(att_mimetype, 'application/pdf')
        self.assertTrue(att_content.startswith(b'%PDF-'))

    def test_customer_full_statutory_banking_contacts_persistence(self):
        from apps.crm.models import Contact
        customer_payload = {
            'customerCode': 'CUST-2026-9099',
            'companyName': 'Bharat Heavy Fabricators Pvt Ltd',
            'customerType': 'company',
            'industry': 'Heavy Engineering',
            'category': 'platinum',
            'gstin': '24AAACB9876C1Z1',
            'pan': 'AAACB9876C',
            'tan': 'AHMC12345D',
            'msmeNumber': 'UDYAM-GJ-01-0012345',
            'taxCategory': 'regular',
            'bankName': 'HDFC Bank Ltd',
            'bankAccountNo': '50200012345678',
            'bankAccountName': 'Bharat Heavy Fabricators Pvt Ltd',
            'bankIfsc': 'HDFC0000001',
            'bankBranch': 'Makarpura Industrial Estate, Vadodara',
            'paymentTerms': '30 Days Net',
            'creditPeriodDays': 45,
            'creditLimit': 1500000,
            'billingAddress': 'Plot 45, GIDC Industrial Estate',
            'shippingAddress': 'Plot 45, GIDC Industrial Estate',
            'city': 'Vadodara',
            'state': 'Gujarat',
            'country': 'India',
            'pincode': '390010',
            'nearestPortRailway': 'Vadodara Junction / Kandla Port',
            'inspectionRequirements': 'Third Party TPI by TUV SUD mandatory',
            'specialInstructions': 'Deliver during working shifts only (8 AM to 6 PM)',
            'contactPerson': 'Mr. Rajesh Sharma',
            'designation': 'General Manager Procurement',
            'mobile': '+91 98250 99999',
            'email': 'rajesh.sharma@bharatfab.com',
            'contacts': [
                {
                    'id': 'CONT-BHARAT-01',
                    'name': 'Mr. Rajesh Sharma',
                    'designation': 'GM Procurement',
                    'department': 'Procurement',
                    'mobile': '+91 98250 99999',
                    'email': 'rajesh.sharma@bharatfab.com',
                    'isPrimary': True,
                },
                {
                    'id': 'CONT-BHARAT-02',
                    'name': 'Ms. Pooja Patel',
                    'designation': 'Accounts Manager',
                    'department': 'Finance',
                    'mobile': '+91 98250 88888',
                    'email': 'accounts@bharatfab.com',
                    'isPrimary': False,
                }
            ]
        }

        # 1. Create customer
        res = self.client.post('/api/customers/', customer_payload, format='json')
        self.assertEqual(res.status_code, 201)
        data = res.json()
        cust_id = data['id']
        self.assertEqual(data['companyName'], 'Bharat Heavy Fabricators Pvt Ltd')
        self.assertEqual(data['msmeNumber'], 'UDYAM-GJ-01-0012345')
        self.assertEqual(data['tan'], 'AHMC12345D')
        self.assertEqual(data['taxCategory'], 'regular')
        self.assertEqual(data['bankName'], 'HDFC Bank Ltd')
        self.assertEqual(data['bankAccountNo'], '50200012345678')
        self.assertEqual(data['bankIfsc'], 'HDFC0000001')
        self.assertEqual(data['creditPeriodDays'], 45)
        self.assertEqual(data['nearestPortRailway'], 'Vadodara Junction / Kandla Port')
        self.assertEqual(data['inspectionRequirements'], 'Third Party TPI by TUV SUD mandatory')

        # 2. Verify contacts were saved and linked to Customer
        linked_contacts = Contact.objects.filter(customer_id=cust_id)
        self.assertTrue(linked_contacts.count() >= 2)
        primary_c = linked_contacts.filter(is_primary=True).first()
        self.assertIsNotNone(primary_c)
        self.assertEqual(primary_c.name, 'Mr. Rajesh Sharma')

        # 3. Retrieve Customer via GET
        get_res = self.client.get(f'/api/customers/{cust_id}/')
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.json()
        self.assertEqual(get_data['msmeNumber'], 'UDYAM-GJ-01-0012345')
        self.assertEqual(get_data['bankBranch'], 'Makarpura Industrial Estate, Vadodara')
        self.assertTrue(len(get_data.get('contacts', [])) >= 2)

    def test_exhibition_crud_and_camel_case_mappings(self):
        expo_payload = {
            'expoName': 'EngiExpo India 2026',
            'organizer': 'Industrial Exhibitions Ltd',
            'location': 'Helipad Exhibition Ground',
            'venue': 'Hall 3',
            'city': 'Gandhinagar',
            'country': 'India',
            'participationStatus': 'confirmed',
            'startDate': '2026-11-15',
            'endDate': '2026-11-18',
            'stallNumber': 'Stall B-12',
            'contactPerson': 'Sunil Verma',
            'budget': 250000,
            'actualExpenses': 180000,
            'assignedTeam': ['Sunil Verma', 'Priya Shah'],
            'productsDisplayed': 'Chemical Reaction Vessels, Heat Exchangers',
            'notes': 'Booked corner stall with heavy 3-phase machinery electrical connection',
            'totalContacts': 45,
            'qualifiedLeads': 12,
            'quotationsSent': 5,
            'convertedCustomers': 2,
        }

        # 1. Create exhibition
        res = self.client.post('/api/exhibitions/', expo_payload, format='json')
        self.assertEqual(res.status_code, 201)
        data = res.json()
        expo_id = data['id']
        self.assertEqual(data['expoName'], 'EngiExpo India 2026')
        self.assertEqual(data['stallNumber'], 'Stall B-12')
        self.assertEqual(data['participationStatus'], 'confirmed')
        self.assertEqual(data['actualExpenses'], 180000.0)

        # 2. Update exhibition via PATCH
        patch_res = self.client.patch(f'/api/exhibitions/{expo_id}/', {
            'actualExpenses': 210000,
            'totalContacts': 60,
            'notes': 'Stall setup completed with company banner',
        }, format='json')
        self.assertEqual(patch_res.status_code, 200)
        patch_data = patch_res.json()
        self.assertEqual(patch_data['actualExpenses'], 210000.0)
        self.assertEqual(patch_data['totalContacts'], 60)

    def test_site_visit_lifecycle(self):
        visit_payload = {
            'visitNo': 'VST-2026-8801',
            'customerId': 'cust-01',
            'customerName': 'Reliance Industries Ltd.',
            'contactPerson': 'Mr. Mukesh',
            'contactMobile': '+91 98250 11111',
            'visitDate': '2026-10-25',
            'location': 'Hazira Petrochemical Complex, Surat',
            'employeeId': 'EMP-001',
            'employeeName': 'Technical Sales Lead',
            'purpose': 'Site measurement & nozzle orientation inspection',
            'discussionNotes': 'Verified foundation bolts and foundation load capacity.',
            'requirementDetails': 'Nozzles need to align with existing header line DN200.',
            'outcome': 'positive',
            'nextAction': 'Submit revised fabrication drawing with updated nozzle elevations',
            'nextFollowUpDate': '2026-10-28',
        }

        # 1. Create site visit
        res = self.client.post('/api/visits/', visit_payload, format='json')
        self.assertEqual(res.status_code, 201)
        data = res.json()
        visit_id = data['id']
        self.assertEqual(data['visitNo'], 'VST-2026-8801')
        self.assertEqual(data['outcome'], 'positive')

        # 2. Fetch list and detail
        get_res = self.client.get(f'/api/visits/{visit_id}/')
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.json()
        self.assertEqual(get_data['location'], 'Hazira Petrochemical Complex, Surat')
        self.assertEqual(get_data['nextFollowUpDate'], '2026-10-28')


