from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounting import posting, reports
from apps.accounting.ledger_models import LedgerEntry
from apps.accounting.models import SalesInvoice

IN_FY = date(reports.fy_range()[0].year, 6, 15)


class AccountingSoftDeleteTests(APITestCase):
    """Deleting an accounting document hides it AND removes its ledger postings; restoring posts them again."""

    def setUp(self):
        posting.seed_master()
        self.client.force_authenticate(
            get_user_model().objects.create_superuser(username='acc_sd_admin', password='Test@12345', first_name='Acc'))
        self.inv = SalesInvoice.objects.create(
            id='SD1', invoice_number='SD1', invoice_date=IN_FY, due_date=IN_FY, customer_id='C1', customer_name='Namkeen Co',
            taxable_amount=100000, cgst_amount=9000, sgst_amount=9000, grand_total=118000, status='Posted')

    def entries(self):
        return LedgerEntry.objects.filter(source_type='SalesInvoice', source_id='SD1').count()

    def test_delete_unposts_and_restore_reposts(self):
        self.assertGreater(self.entries(), 0)

        r = self.client.delete('/api/sales-invoices/SD1/')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.entries(), 0)                                    # ledger no longer shows it
        row = SalesInvoice.all_objects.get(pk='SD1')
        self.assertFalse(row.is_active)                                        # but the invoice is still there
        self.assertTrue(row.deleted_by)
        self.assertFalse(SalesInvoice.objects.filter(pk='SD1').exists())

        r = self.client.post('/api/sales-invoices/SD1/restore/')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertGreater(self.entries(), 0)                                  # posted again
        self.assertTrue(SalesInvoice.objects.filter(pk='SD1').exists())

    def test_saving_a_deleted_invoice_never_posts(self):
        self.client.delete('/api/sales-invoices/SD1/')
        row = SalesInvoice.all_objects.get(pk='SD1')
        row.remarks = 'touched'
        row.save()
        self.assertEqual(self.entries(), 0)
