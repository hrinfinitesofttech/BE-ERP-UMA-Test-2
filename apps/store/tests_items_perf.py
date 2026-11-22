from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.store.models import ItemMaster, StockBalance


class ItemMasterListPerformanceTests(TestCase):
    """The item list used to run 2-4 StockBalance queries per item (thousands of queries)."""

    def setUp(self):
        self.user = User.objects.create(id='EMP-S', username='s', first_name='S', last_name='T', role_type='admin')
        self.c = APIClient()
        self.c.force_authenticate(self.user)

    def _make(self, n):
        for i in range(n):
            ItemMaster.objects.create(id=f'I{i}', item_code=f'C{i}', item_name=f'Item {i}', category='RM')
        # stock by code (+ a duplicate row: the first one must win), and one matched only by name
        StockBalance.objects.create(id='S0a', item_id='I0', item_code='C0', item_name='Item 0', available_quantity=5)
        StockBalance.objects.create(id='S0b', item_id='I0', item_code='C0', item_name='Item 0', available_quantity=99)
        StockBalance.objects.create(id='S1', item_id='X', item_code='OTHER', item_name='ITEM 1', available_quantity=7)

    def _list(self):
        r = self.c.get('/api/items/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        return data if isinstance(data, list) else data['results']

    def test_values_match_per_object_logic(self):
        self._make(4)
        rows = {x['id']: x for x in self._list()}
        self.assertEqual(rows['I0']['currentStock'], 5.0)   # first row for the code
        self.assertEqual(rows['I1']['currentStock'], 7.0)   # fallback: case-insensitive name
        self.assertEqual(rows['I2']['currentStock'], 0.0)
        # single-object endpoint still agrees with the list
        for item_id, row in rows.items():
            single = self.c.get(f'/api/items/{item_id}/').json()
            self.assertEqual(single['currentStock'], row['currentStock'])

    def test_query_count_does_not_grow_with_items(self):
        self._make(5)
        with CaptureQueriesContext(connection) as small:
            self._list()
        for i in range(5, 60):
            ItemMaster.objects.create(id=f'I{i}', item_code=f'C{i}', item_name=f'Item {i}', category='RM')
        with CaptureQueriesContext(connection) as big:
            self._list()
        self.assertEqual(len(small), len(big), f'queries grew: {len(small)} -> {len(big)}')
