from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class QuotationPriceMandatoryTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(
            get_user_model().objects.create_superuser(username='quo_price_user', password='Test@12345'))

    def payload(self, rate, number='QT-2026-7001'):
        return {
            'quotationNumber': number, 'customerId': 'c1', 'customerName': 'Acme', 'validUntil': '2026-12-31',
            'revisions': [{
                'revisionNumber': 'Rev-00', 'date': '2026-11-01', 'status': 'draft', 'grandTotal': 100,
                'items': [{'id': 'i1', 'productName': 'Fryer', 'quantity': 2, 'unit': 'Nos', 'rate': rate,
                           'taxPercent': 18, 'amount': 0}],
            }],
        }

    def test_zero_or_missing_price_is_rejected(self):
        for bad in (0, '', None, '0', -5):
            r = self.client.post('/api/quotations/', self.payload(bad), format='json')
            self.assertEqual(r.status_code, 400, f'rate={bad!r} -> {r.content}')
            self.assertIn('Price', r.json()['error'])

    def test_one_unpriced_item_blocks_the_whole_quotation(self):
        p = self.payload(1000)
        p['revisions'][0]['items'].append({'id': 'i2', 'productName': 'Boiler', 'quantity': 1, 'rate': 0})
        r = self.client.post('/api/quotations/', p, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['items'], ['Boiler'])

    def test_priced_quotation_is_created(self):
        r = self.client.post('/api/quotations/', self.payload(250000, 'QT-2026-7002'), format='json')
        self.assertEqual(r.status_code, 201, r.content)
