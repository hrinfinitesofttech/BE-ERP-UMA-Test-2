from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.crm.models import Customer, Lead


class SoftDeleteTests(APITestCase):
    def setUp(self):
        U = get_user_model()
        self.admin = U.objects.create_superuser(username='sd_admin', password='Test@12345', first_name='Sd', last_name='Admin')
        self.staff = U.objects.create_user(username='sd_staff', password='Test@12345', role_type='employee')
        self.client.force_authenticate(self.admin)

    def make_lead(self, company='Acme', mobile='9825012345'):
        r = self.client.post('/api/leads/', {'companyName': company, 'contactPerson': 'Ravi', 'mobile': mobile,
                                             'email': 'r@acme.com', 'address': 'Vadodara', 'source': 'phone'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()

    def test_delete_is_soft_and_record_is_hidden_everywhere(self):
        lead = self.make_lead()
        r = self.client.delete(f"/api/leads/{lead['id']}/")
        self.assertEqual(r.status_code, 204)

        # still in the database, flagged, with who and when
        row = Lead.all_objects.get(pk=lead['id'])
        self.assertFalse(row.is_active)
        self.assertEqual(row.deleted_by, 'Sd Admin')
        self.assertIsNotNone(row.deleted_at)

        # hidden from list, detail and the default manager
        self.assertNotIn(lead['id'], [x['id'] for x in self.client.get('/api/leads/').json()])
        self.assertEqual(self.client.get(f"/api/leads/{lead['id']}/").status_code, 404)
        self.assertFalse(Lead.objects.filter(pk=lead['id']).exists())
        self.assertEqual(Lead.all_objects.filter(pk=lead['id']).count(), 1)

    def test_deleted_number_is_never_reused(self):
        first = self.make_lead('One')
        self.client.delete(f"/api/leads/{first['id']}/")
        second = self.make_lead('Two', '9825099999')
        self.assertNotEqual(first['id'], second['id'])
        self.assertNotEqual(first['leadNo'], second['leadNo'])

    def test_queryset_delete_is_soft_too(self):
        a, b = self.make_lead('A'), self.make_lead('B', '9825000001')
        Lead.objects.filter(pk__in=[a['id'], b['id']]).delete()
        self.assertEqual(Lead.objects.filter(pk__in=[a['id'], b['id']]).count(), 0)
        self.assertEqual(Lead.all_objects.filter(pk__in=[a['id'], b['id']], is_active=False).count(), 2)

    def test_deleted_records_list_and_restore(self):
        lead = self.make_lead()
        self.client.delete(f"/api/leads/{lead['id']}/")

        listing = self.client.get('/api/core/deleted-records/?model=crm.Lead').json()
        self.assertEqual([r['id'] for r in listing], [lead['id']])
        self.assertEqual(listing[0]['deletedBy'], 'Sd Admin')
        self.assertEqual(self.client.get('/api/deleted-records/?search=nomatch-zzz').json(), [])

        r = self.client.post('/api/core/deleted-records/', {'model': 'crm.Lead', 'id': lead['id']}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.client.get(f"/api/leads/{lead['id']}/").status_code, 200)
        self.assertEqual(self.client.get('/api/core/deleted-records/?model=crm.Lead').json(), [])
        self.assertEqual(self.client.post('/api/core/deleted-records/', {'model': 'crm.Lead', 'id': lead['id']}, format='json').status_code, 400)

    def test_restore_action_on_the_viewset(self):
        lead = self.make_lead()
        self.client.delete(f"/api/leads/{lead['id']}/")
        self.assertEqual(self.client.post(f"/api/leads/{lead['id']}/restore/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/leads/{lead['id']}/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/leads/{lead['id']}/restore/").status_code, 400)
        self.assertEqual(self.client.post('/api/leads/nope/restore/').status_code, 404)

    def test_ordinary_employee_cannot_see_or_restore_deleted_records(self):
        lead = self.make_lead()
        self.client.delete(f"/api/leads/{lead['id']}/")
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/core/deleted-records/').status_code, 403)
        self.assertEqual(self.client.post(f"/api/leads/{lead['id']}/restore/").status_code, 403)
        self.assertEqual(self.client.post('/api/core/deleted-records/', {'model': 'crm.Lead', 'id': lead['id']}, format='json').status_code, 403)

    def test_converted_customer_survives_and_hard_delete_is_explicit(self):
        lead = self.make_lead()
        cust = self.client.post(f"/api/leads/{lead['id']}/convert/").json()['customer']
        self.client.delete(f"/api/customers/{cust['id']}/")
        self.assertFalse(Customer.objects.filter(pk=cust['id']).exists())
        self.assertTrue(Customer.all_objects.filter(pk=cust['id']).exists())
        Customer.all_objects.filter(pk=cust['id']).hard_delete()
        self.assertFalse(Customer.all_objects.filter(pk=cust['id']).exists())
