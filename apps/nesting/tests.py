from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.designer.models import DesignJob, Drawing2D


class NestingFlowTests(APITestCase):
    def setUp(self):
        U = get_user_model()
        self.nesting = U.objects.create_user(username='nest_user', password='x', first_name='Nest', last_name='User')
        self.prod = U.objects.create_user(username='prod_user', password='x', first_name='Prod', last_name='User')
        self.dj = DesignJob.objects.create(
            id='DES-T-1', design_job_number='DES-T-1', project_id='PRJ-T-1', project_number='PRJ-T-1',
            job_number='JOB-T-1', customer_id='C1', customer_name='Acme', product_name='Pressure Vessel',
            delivery_date='2026-12-31', created_date='2026-11-01')
        Drawing2D.objects.create(design_job_id='DES-T-1', drawing_number='DWG-1', title='Shell Plate',
                                 file_format='DXF', file_url='data:application/dxf;base64,AAAA')
        Drawing2D.objects.create(design_job_id='DES-T-1', drawing_number='DWG-2', title='GA',
                                 file_format='PDF', file_url='data:application/pdf;base64,BBBB')

    def share(self):
        self.client.force_authenticate(self.nesting)
        return self.client.post('/api/nesting/jobs/share-from-design/', {'designJobId': 'DES-T-1'}, format='json')

    def test_design_files_listed_and_shared(self):
        self.client.force_authenticate(self.nesting)
        r = self.client.get('/api/nesting/jobs/design-files/?designJobId=DES-T-1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual({f['fileType'] for f in r.json()['files']}, {'DXF', 'PDF'})
        r = self.share()
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data['status'], 'received')
        self.assertEqual(len(data['files']), 2)
        self.assertEqual(data['jobNumber'], 'JOB-T-1')
        # sharing again must reuse the open job, not create a duplicate
        r2 = self.share()
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()['id'], data['id'])
        self.assertEqual(len(r2.json()['files']), 2)

    def test_share_requires_files_and_known_job(self):
        self.client.force_authenticate(self.nesting)
        self.assertEqual(self.client.post('/api/nesting/jobs/share-from-design/', {'designJobId': 'nope'},
                                          format='json').status_code, 404)

    def test_full_cut_handover_rework_flow_and_estimate(self):
        job_id = self.share().json()['id']
        # nesting engineer takes the job and defines the parts
        self.client.post(f'/api/nesting/jobs/{job_id}/start/', {'cuttingMachine': 'Plasma-1'}, format='json')
        t = self.client.post('/api/nesting/tasks/', {
            'jobId': job_id, 'partName': 'Shell Plate', 'thicknessMm': 10, 'requiredQty': 10}, format='json')
        self.assertEqual(t.status_code, 201, t.content)
        tid = t.json()['id']

        # cannot hand over before cutting, cannot over-cut
        self.assertEqual(self.client.post(f'/api/nesting/tasks/{tid}/hand-over/', {'qty': 1}, format='json').status_code, 400)
        self.assertEqual(self.client.post(f'/api/nesting/tasks/{tid}/log-cutting/', {'qty': 11}, format='json').status_code, 400)

        r = self.client.post(f'/api/nesting/tasks/{tid}/log-cutting/', {'qty': 6}, format='json')
        self.assertEqual((r.json()['cutQty'], r.json()['status']), (6, 'in_progress'))
        self.assertEqual(self.client.get(f'/api/nesting/jobs/{job_id}/').json()['status'], 'cutting')
        self.client.post(f'/api/nesting/tasks/{tid}/log-cutting/', {'qty': 4}, format='json')
        self.assertEqual(self.client.get(f'/api/nesting/jobs/{job_id}/').json()['status'], 'completed')

        # hand over all 10 to production
        ho = self.client.post(f'/api/nesting/tasks/{tid}/hand-over/', {'qty': 10}, format='json')
        self.assertEqual(ho.status_code, 201)
        hid = ho.json()['id']
        self.assertEqual(self.client.post(f'/api/nesting/tasks/{tid}/hand-over/', {'qty': 1}, format='json').status_code, 400)
        self.assertEqual(self.client.get(f'/api/nesting/jobs/{job_id}/').json()['status'], 'handed_over')

        # nesting cannot review its own hand-over
        self.assertEqual(self.client.post(f'/api/nesting/handovers/{hid}/accept/', {}, format='json').status_code, 403)

        # production accepts 6, rejects 3 (needs a reason) and sends 1 back for rework
        self.client.force_authenticate(self.prod)
        self.assertEqual(self.client.post(f'/api/nesting/handovers/{hid}/reject/', {'qty': 3}, format='json').status_code, 400)
        acc = self.client.post(f'/api/nesting/handovers/{hid}/accept/', {'qty': 6}, format='json')
        self.assertEqual((acc.status_code, acc.json()['qty'], acc.json()['status']), (200, 6, 'accepted'))
        rej = self.client.post(f'/api/nesting/handovers/{hid}/reject/', {'qty': 3, 'reason': 'Wrong size'}, format='json')
        self.assertEqual(rej.json()['status'], 'rejected')
        self.assertTrue(rej.json()['needsAttention'])
        rw = self.client.post(f'/api/nesting/handovers/{hid}/rework/', {'qty': 1, 'reason': 'Dross on edge'}, format='json')
        self.assertEqual(rw.json()['status'], 'reworkRequired' if False else 'rework_required')

        job = self.client.get(f'/api/nesting/jobs/{job_id}/').json()
        self.assertEqual(job['status'], 'rework')
        self.assertEqual(job['summary']['reworkQty'], 4)
        self.assertEqual(job['summary']['acceptedQty'], 6)
        self.assertEqual(self.client.get('/api/nesting/handovers/?attention=1').json().__len__(), 2)

        # nesting redoes the work and re-submits everything -> back with production
        self.client.force_authenticate(self.nesting)
        for entry in (rej.json()['id'], rw.json()['id']):
            r = self.client.post(f'/api/nesting/handovers/{entry}/resubmit/', {}, format='json')
            self.assertEqual(r.status_code, 201, r.content)
            self.assertEqual(r.json()['kind'], 'rework')
        self.assertEqual(self.client.post(f'/api/nesting/handovers/{rej.json()["id"]}/resubmit/', {}, format='json').status_code, 400)
        job = self.client.get(f'/api/nesting/jobs/{job_id}/').json()
        self.assertEqual(job['status'], 'handed_over')
        self.assertEqual(job['summary']['reworkQty'], 0)
        # re-handing over must not create phantom parts: nothing more is available to hand over
        task = self.client.get(f'/api/nesting/tasks/{tid}/').json()
        self.assertEqual(task['quantities']['availableToHandOverQty'], 0)
        self.assertEqual(task['quantities']['awaitingReviewQty'], 4)

        # production accepts the reworked parts -> job closed
        self.client.force_authenticate(self.prod)
        for h in self.client.get('/api/nesting/handovers/?status=handed_over').json():
            self.assertEqual(self.client.post(f'/api/nesting/handovers/{h["id"]}/accept/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.get(f'/api/nesting/jobs/{job_id}/').json()['status'], 'closed')

        # sheets: 4 issued, 3 used, 1 untouched goes back, 50 kg of reusable offcuts
        self.client.force_authenticate(self.nesting)
        s = self.client.post('/api/nesting/sheet-usage/', {
            'jobId': job_id, 'thicknessMm': 10, 'sheetsIssued': 4, 'sheetsUsed': 3,
            'leftoverWeightKg': 50, 'ratePerKg': 60}, format='json')
        self.assertEqual(s.status_code, 201, s.content)
        sd = s.json()
        self.assertEqual(sd['sheetsLeftover'], 1)          # derived: issued - used
        self.assertEqual(sd['unitWeightKg'], 245.31)       # 2.5 x 1.25 x 0.010 m x 7850
        self.assertEqual(sd['grossWeightKg'], 735.94)
        self.assertEqual(sd['netWeightKg'], 685.94)
        self.assertEqual(sd['netCost'], round(685.94 * 60, 2))
        bad = self.client.post('/api/nesting/sheet-usage/', {
            'jobId': job_id, 'thicknessMm': 10, 'sheetsIssued': 2, 'sheetsUsed': 3}, format='json')
        self.assertEqual(bad.status_code, 400)

        summ = self.client.get('/api/nesting/jobs/project-summary/?projectId=PRJ-T-1').json()
        self.assertEqual(len(summ), 1)
        self.assertEqual(summ[0]['totals']['sheetsUsed'], 3)
        self.assertEqual(summ[0]['totals']['netWeightKg'], 685.94)
        self.assertEqual(summ[0]['byThickness'][0]['sheetsLeftover'], 1)

        stats = self.client.get('/api/nesting/jobs/stats/').json()
        self.assertEqual(stats['openRework'], 0)

    def test_requires_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/nesting/jobs/').status_code, 401)
