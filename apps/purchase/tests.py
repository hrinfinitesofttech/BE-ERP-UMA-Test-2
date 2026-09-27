from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from apps.purchase.models import Supplier, PurchaseOrder
from apps.store.models import ItemMaster, GoodsReceiptNote, StockBalance, StockLedgerEntry


class Phase4PurchaseStoreTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command('seed_phase1')
        call_command('seed_phase2')
        call_command('seed_phase3')
        call_command('seed_phase4')

    def test_suppliers_list_and_camel_case(self):
        response = self.client.get('/api/suppliers/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 4)
        sup = data[0]
        self.assertIn('vendorCode', sup)
        self.assertIn('paymentTerms', sup)

    def test_purchase_order_details_and_approval(self):
        po = PurchaseOrder.objects.first()
        response = self.client.get(f'/api/purchase-orders/{po.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['poNumber'], po.po_number)
        self.assertIn('grandTotal', data)

        # Test approval action
        app_res = self.client.post(f'/api/purchase-orders/{po.id}/approve/', {
            'approvedBy': 'Rajesh Patel',
        }, format='json')
        self.assertEqual(app_res.status_code, 200)
        app_data = app_res.json()
        self.assertEqual(app_data['status'], 'approved')

    def test_item_master_list(self):
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 4)
        first_item = data[0]
        self.assertIn('itemCode', first_item)
        self.assertIn('unitCost', first_item)
        self.assertIn('hsnSac', first_item)

    def test_grn_and_inward_qc(self):
        response = self.client.get('/api/grns/GRN-2026-0018/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['grnNumber'], 'GRN-2026-0018')
        self.assertEqual(data['qcStatus'], 'Pass')
        self.assertEqual(data['status'], 'Accepted')

    def test_stock_balance_and_material_issue(self):
        # 1. Verify initial stock balance
        stock_res = self.client.get('/api/stock/stk-rm-ss316l-pl-8mm/')
        self.assertEqual(stock_res.status_code, 200)
        stk_data = stock_res.json()
        self.assertEqual(stk_data['quantity'], 1850)

        # 2. Issue 500 Kg to fabrication shopfloor
        issue_res = self.client.post('/api/material-issues/', {
            'projectId': 'PRJ-2026-0042',
            'jobNumber': 'JOB-2026-0042',
            'issuedTo': 'Suresh Chauhan (Fit-up Supervisor)',
            'issueDate': '2026-09-08',
            'warehouseId': 'wh-main',
            'items': [
                {'itemCode': 'RM-SS316L-PL-8MM', 'issuedQty': 500, 'unit': 'Kg'}
            ],
            'notes': 'Issued for vessel shell plate rolling',
        }, format='json')
        self.assertEqual(issue_res.status_code, 201)

        # 3. Check stock deducted to 1350 Kg
        stock_after = self.client.get('/api/stock/stk-rm-ss316l-pl-8mm/').json()
        self.assertEqual(stock_after['quantity'], 1350)
