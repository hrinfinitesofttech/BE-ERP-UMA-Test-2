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


class QuotationRevisionEditTests(APITestCase):
    """Quantity / unit rate / GST of a draft revision can be edited; approved ones are locked."""

    def setUp(self):
        self.client.force_authenticate(
            get_user_model().objects.create_superuser(username='quo_edit_user', password='Test@12345'))
        r = self.client.post('/api/quotations/', {
            'quotationNumber': 'QT-2026-7100', 'customerId': 'c1', 'customerName': 'Acme', 'validUntil': '2026-12-31',
            'revisions': [{
                'revisionNumber': 'Rev-00', 'date': '2026-11-01', 'status': 'draft', 'grandTotal': 1180,
                'items': [{'id': 'i1', 'productName': 'Fryer', 'quantity': 1, 'unit': 'Nos', 'rate': 1000,
                           'discountPercent': 0, 'taxPercent': 18, 'amount': 1180}],
            }],
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.qid = r.json()['id']

    def edit(self, items, rev='Rev-00'):
        return self.client.post(f'/api/quotations/{self.qid}/update-revision/',
                                {'revisionNumber': rev, 'items': items}, format='json')

    def test_edit_recalculates_amounts_and_totals(self):
        r = self.edit([{'id': 'i1', 'quantity': 3, 'rate': 2500, 'discountPercent': 10, 'taxPercent': 12}])
        self.assertEqual(r.status_code, 200, r.content)
        rev = r.json()['revisions'][0]
        # 3 x 2500 = 7500, less 10% = 6750, GST 12% = 810 -> 7560
        self.assertEqual(rev['items'][0]['amount'], 7560)
        self.assertEqual((rev['subTotal'], rev['taxAmount'], rev['grandTotal']), (6750, 810, 7560))
        self.assertEqual(r.json()['grandTotal'], 7560)          # quotation level total follows the current revision
        self.assertEqual(rev['items'][0]['productName'], 'Fryer')  # untouched fields are kept

    def test_price_is_mandatory_and_quantity_positive(self):
        self.assertEqual(self.edit([{'id': 'i1', 'quantity': 1, 'rate': 0, 'taxPercent': 18}]).status_code, 400)
        self.assertEqual(self.edit([{'id': 'i1', 'quantity': 0, 'rate': 100, 'taxPercent': 18}]).status_code, 400)

    def test_items_cannot_be_added_or_removed(self):
        two = [{'id': 'i1', 'quantity': 1, 'rate': 5}, {'id': 'i2', 'quantity': 1, 'rate': 5}]
        self.assertEqual(self.edit(two).status_code, 400)

    def test_approved_revision_is_locked_and_next_revision_is_editable(self):
        self.client.post(f'/api/quotations/{self.qid}/update-status/', {'revisionNumber': 'Rev-00', 'status': 'approved'}, format='json')
        locked = self.edit([{'id': 'i1', 'quantity': 2, 'rate': 1000, 'taxPercent': 18}])
        self.assertEqual(locked.status_code, 400)
        self.assertEqual(locked.json()['code'], 'REVISION_LOCKED')
        # create next revision (copy) -> draft -> editable
        rev1 = {'revisionNumber': 'Rev-01', 'date': '2026-11-02', 'status': 'draft', 'grandTotal': 1180,
                'items': [{'id': 'i1', 'productName': 'Fryer', 'quantity': 1, 'unit': 'Nos', 'rate': 1000,
                           'discountPercent': 0, 'taxPercent': 18, 'amount': 1180}]}
        self.assertEqual(self.client.post(f'/api/quotations/{self.qid}/add-revision/', rev1, format='json').status_code, 200)
        ok = self.edit([{'id': 'i1', 'quantity': 2, 'rate': 1500, 'taxPercent': 18}], rev='Rev-01')
        self.assertEqual(ok.status_code, 200, ok.content)
        self.assertEqual(ok.json()['grandTotal'], 3540)
        # the approved Rev-00 is untouched
        self.assertEqual(ok.json()['revisions'][0]['grandTotal'], 1180)
