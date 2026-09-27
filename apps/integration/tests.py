from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from .models import ApprovalItem, ERPAlertItem
from apps.production.models import ManufacturingJob


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_approval_lifecycle(self):
        appr = ApprovalItem.objects.create(
            id='APPR-TEST-01',
            category='Purchase Order',
            title='Test PO Approval',
            record_number='PO-TEST-001',
            requester_name='Pooja Shah',
            request_date=date(2026, 9, 20),
            amount=250000.0,
            status='Pending'
        )

        res = self.client.post(f'/api/approvals/{appr.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        appr.refresh_from_db()
        self.assertEqual(appr.status, 'Approved')

    def test_alert_mark_read(self):
        alert = ERPAlertItem.objects.create(
            id='ALT-TEST-01',
            module='Production',
            severity='Warning',
            title='Machine Maintenance Due',
            description='Test description',
            is_read=False
        )

        res = self.client.post(f'/api/alerts/{alert.id}/mark-read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        self.assertTrue(alert.is_read)

    def test_job_360_api(self):
        # Create a test job
        job = ManufacturingJob.objects.create(
            id='MJ-JOB-TEST-01',
            job_number='JOB-TEST-01',
            product_name='Test Pressure Vessel 50KL',
            production_progress=40,
            status='In Production'
        )

        res = self.client.get(f'/api/job-360/{job.job_number}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        
        # Verify 360 structure
        self.assertIn('header', data)
        self.assertEqual(data['header']['jobNumber'], 'JOB-TEST-01')
        self.assertEqual(data['header']['productName'], 'Test Pressure Vessel 50KL')
        self.assertIn('crm', data)
        self.assertIn('project', data)
        self.assertIn('design', data)
        self.assertIn('purchase', data)
        self.assertIn('store', data)
        self.assertIn('production', data)
        self.assertIn('quality', data)
        self.assertIn('dispatch', data)
        self.assertIn('accounts', data)
        self.assertIn('service', data)
        self.assertIn('documents', data)
        self.assertIn('timeline', data)
