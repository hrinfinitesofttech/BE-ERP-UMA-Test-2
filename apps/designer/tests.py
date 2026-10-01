from django.test import TestCase
from rest_framework.test import APIClient
from apps.designer.models import DesignJob, CustomerRequirement, Drawing2D, Design3DModel, BOMHeader


class DesignerAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_design_job_camel_case_and_persistence(self):
        payload = {
            'designJobNumber': 'DES-2026-0005',
            'projectId': 'PRJ-2026-0041',
            'projectNumber': 'PRJ-2026-0041',
            'jobNumber': 'JOB-2026-0051',
            'customerId': 'CUST-2026-0018',
            'customerName': 'Ravi Aluminium PVT LTD',
            'customerPoNumber': 'PO/1234/123',
            'salesOrderNumber': 'SO-2026-0082',
            'productName': 'Custom Equipment (Ref QT-2026-0133)',
            'machineType': 'Process Equipment Unit',
            'quantity': 1,
            'deliveryDate': '2026-11-30',
            'designManager': 'Dharmesh Joshi',
            'assignedDesigner': 'Dharmesh Joshi',
            'priority': 'high',
            'requiredDate': '2026-11-30',
            'status': 'assigned',
            'remarks': 'Test design job',
            'activeRevision': 'REV-00',
            'createdDate': '2026-10-01',
        }

        # 1. Post to /api/designer/jobs/
        res = self.client.post('/api/designer/jobs/', payload, format='json')
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data['id'], 'DES-2026-0005')
        self.assertEqual(data['customerName'], 'Ravi Aluminium PVT LTD')
        self.assertEqual(data['productName'], 'Custom Equipment (Ref QT-2026-0133)')

        # 2. Check in database
        db_job = DesignJob.objects.filter(id='DES-2026-0005').first()
        self.assertIsNotNone(db_job)
        self.assertEqual(db_job.customer_name, 'Ravi Aluminium PVT LTD')
        self.assertEqual(db_job.job_number, 'JOB-2026-0051')

        # 3. Create second job with duplicate or empty ID -> auto increment to next sequence
        res2 = self.client.post('/api/designer/jobs/', payload, format='json')
        self.assertEqual(res2.status_code, 201)
        data2 = res2.json()
        self.assertEqual(data2['id'], 'DES-2026-0006')

        # Check in database
        self.assertEqual(DesignJob.objects.count(), 2)

        # 4. Get list endpoint
        res3 = self.client.get('/api/designer/jobs/')
        self.assertEqual(res3.status_code, 200)
        jobs_list = res3.json()
        self.assertEqual(len(jobs_list), 2)
