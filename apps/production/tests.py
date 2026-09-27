from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import ManufacturingJob, WorkCenter, WorkOrder, FinishedGoodsItem
from apps.maintenance.models import InternalAsset, ServiceRequest
from apps.hr.models import Designation, LeaveRequest, PayrollRecord


class ProductionMaintenanceHRTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_production_jobs_list(self):
        res = self.client.get('/api/manufacturing-jobs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Verify response structure and camelCase keys
        items = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        self.assertIsInstance(items, list)
        if len(items) > 0:
            item = items[0]
            self.assertIn('jobNumber', item)
            self.assertIn('productName', item)
            self.assertIn('productionProgress', item)

    def test_work_order_release_action(self):
        # Create a work order
        wo = WorkOrder.objects.create(
            id='WO-TEST-001',
            work_order_number='WO-TEST-001',
            product_name='Test Exchanger',
            production_quantity=1.0,
            status='Draft'
        )
        res = self.client.post(f'/api/work-orders/{wo.id}/release/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        wo.refresh_from_db()
        self.assertEqual(wo.status, 'Released')

    def test_finished_goods_qc_pass(self):
        fg = FinishedGoodsItem.objects.create(
            id='FG-TEST-001',
            finished_goods_number='FG-TEST-001',
            product_name='Storage Vessel',
            quantity=1.0,
            completion_date='2026-09-27',
            qc_status='QC Pending',
            status='Production Complete'
        )
        res = self.client.post(f'/api/finished-goods/{fg.id}/qc-pass/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        fg.refresh_from_db()
        self.assertEqual(fg.qc_status, 'QC Passed')
        self.assertEqual(fg.status, 'Ready for Dispatch')

    def test_service_request_lifecycle(self):
        sr = ServiceRequest.objects.create(
            id='SR-TEST-001',
            request_number='SR-TEST-001',
            request_date='2026-09-27',
            customer_name='Test Refinery',
            machine_name='Reactor 101',
            priority='High',
            status='New'
        )
        # Assign technician
        res = self.client.post(
            f'/api/service-requests/{sr.id}/assign/',
            {'technicianId': 'EMP-003', 'technicianName': 'Sanjay Mehta'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sr.refresh_from_db()
        self.assertEqual(sr.status, 'Assigned')
        self.assertEqual(sr.assigned_technician_id, 'EMP-003')

        # Resolve
        res2 = self.client.post(f'/api/service-requests/{sr.id}/resolve/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        sr.refresh_from_db()
        self.assertEqual(sr.status, 'Resolved')
        self.assertIsNotNone(sr.closed_at)

    def test_hr_leave_approval(self):
        leave = LeaveRequest.objects.create(
            id='LV-TEST-001',
            leave_number='LV-TEST-001',
            employee_id='EMP-001',
            employee_name='Rajesh Patel',
            department='Engineering',
            leave_name='Sick Leave',
            from_date='2026-09-28',
            to_date='2026-09-29',
            number_of_days=2.0,
            reason='Viral Fever',
            applied_date='2026-09-27',
            status='Pending'
        )
        res = self.client.post(
            f'/api/leave-requests/{leave.id}/approve/',
            {'approvedBy': 'HR Lead'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Approved')
        self.assertEqual(leave.approved_by, 'HR Lead')
