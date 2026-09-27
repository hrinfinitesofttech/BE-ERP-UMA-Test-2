from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from apps.projects.models import ProjectJobMaster, ProjectPlanningStage
from apps.designer.models import DesignJob, BOMHeader


class Phase3ProjectDesignTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command('seed_phase1')
        call_command('seed_phase2')
        call_command('seed_phase3')

    def test_project_list_and_camel_case(self):
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 1)
        p = data[0]
        self.assertEqual(p['projectNumber'], 'PRJ-2026-0042')
        self.assertIn('jobNumber', p)
        self.assertIn('targetDeliveryDate', p)
        self.assertIn('progressPercent', p)

    def test_auto_generated_16_planning_stages(self):
        response = self.client.get('/api/planning-stages/?projectId=PRJ-2026-0042')
        self.assertEqual(response.status_code, 200)
        stages = response.json()
        self.assertEqual(len(stages), 16)
        self.assertEqual(stages[0]['name'], 'Order Confirmation & Kickoff')
        self.assertEqual(stages[15]['name'], 'Commercial Invoicing & Dispatch Handover')

    def test_mark_planning_stage_completed(self):
        stage = ProjectPlanningStage.objects.filter(project_id='PRJ-2026-0042', stage_number=3).first()
        response = self.client.post(f'/api/planning-stages/{stage.id}/complete/', {
            'completedBy': 'Dharmesh Joshi',
            'notes': '3D CAD Modeling and GA Drawing approved by client.',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['progress'], 100)

    def test_design_job_and_bom_items(self):
        response = self.client.get('/api/design-jobs/DES-2026-0001/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['designJobNumber'], 'DES-2026-0001')
        self.assertIn('activeRevision', data)

        # Test BOM items
        bom_res = self.client.get('/api/boms/BOM-CRV-10K/')
        self.assertEqual(bom_res.status_code, 200)
        bom_data = bom_res.json()
        self.assertEqual(bom_data['bomNumber'], 'BOM-CRV-10K')
        self.assertTrue(len(bom_data['items']) >= 5)
        first_item = bom_data['items'][0]
        self.assertIn('itemCode', first_item)
        self.assertIn('materialGrade', first_item)

    def test_release_design_to_production(self):
        response = self.client.post('/api/design-jobs/DES-2026-0001/release-to-production/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['job']['status'], 'released_to_production')
