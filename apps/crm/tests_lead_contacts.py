from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.crm.models import Contact, Lead


class LeadAdditionalContactsTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(
            get_user_model().objects.create_superuser(username='lead_contacts_user', password='Test@12345'))

    def create(self, **extra):
        payload = {'companyName': 'Acme Fab', 'contactPerson': 'Ravi', 'mobile': '9825012345',
                   'email': 'ravi@acme.com', 'address': 'Vadodara', 'source': 'phone', **extra}
        return self.client.post('/api/leads/', payload, format='json')

    def test_multiple_contacts_saved_cleaned_and_returned(self):
        r = self.create(additionalContacts=['98250 11111', '9825022222', '9825022222', ''])
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['additionalContacts'], ['9825011111', '9825022222'])
        lead = Lead.objects.get(id=r.json()['id'])
        self.assertEqual(lead.additional_contacts, ['9825011111', '9825022222'])
        got = self.client.get(f"/api/leads/{lead.id}/").json()
        self.assertEqual(got['additionalContacts'], ['9825011111', '9825022222'])
        self.assertEqual(got['mobile'], '9825012345')

    def test_lead_without_extra_contacts_still_works(self):
        r = self.create()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['additionalContacts'], [])

    def test_update_extra_contacts(self):
        lead_id = self.create(additionalContacts=['9825011111']).json()['id']
        r = self.client.patch(f'/api/leads/{lead_id}/', {'additionalContacts': ['9825033333', '9825044444']}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['additionalContacts'], ['9825033333', '9825044444'])
        r = self.client.patch(f'/api/leads/{lead_id}/', {'additionalContacts': []}, format='json')
        self.assertEqual(r.json()['additionalContacts'], [])

    def test_invalid_number_rejected(self):
        r = self.create(additionalContacts=['123'])
        self.assertEqual(r.status_code, 400)

    def test_convert_keeps_extra_numbers_as_customer_contacts(self):
        lead_id = self.create(additionalContacts=['9825011111', '9825022222']).json()['id']
        r = self.client.post(f'/api/leads/{lead_id}/convert/')
        self.assertEqual(r.status_code, 200, r.content)
        cust_id = r.json()['customer']['id']
        nums = sorted(Contact.objects.filter(customer_id=cust_id).values_list('mobile', flat=True))
        self.assertEqual(nums, ['9825011111', '9825022222'])
