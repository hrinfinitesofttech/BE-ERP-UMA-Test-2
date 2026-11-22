from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounting import posting, reports
from apps.accounting.ledger_models import (Ledger, LedgerEntry, StockItem, DepreciationAsset, PaymentRequest, Voucher)
from apps.accounting.models import (SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment, ExpenseEntry)

TODAY = date.today()
# a date inside the current financial year
IN_FY = date(reports.fy_range()[0].year, 6, 15)


class LedgerEngineTests(APITestCase):
    def setUp(self):
        U = get_user_model()
        self.user = U.objects.create_user(username='acct', password='x', email='a@b.c')
        self.client.force_authenticate(self.user)
        posting.seed_master()

    def test_seed_counts_match_excel(self):
        self.assertEqual(DepreciationAsset.objects.count(), 36)
        self.assertEqual(StockItem.objects.filter(category='Finished Goods').count(), 20)
        names = [l.name for l in Ledger.objects.filter(group__name='Direct Expenses')]
        self.assertEqual(len(names), 14)
        self.assertEqual(Ledger.objects.filter(group__name='Indirect Expenses').count(), 25)  # 24 + DEPRECIATION
        # idempotent
        posting.seed_master()
        self.assertEqual(DepreciationAsset.objects.count(), 36)

    def _book(self):
        Ledger.objects.filter(name='Kantibhai Manvar Capital A/C-50%').update(opening_balance=500000)
        Ledger.objects.filter(name='Pankaj Manvar-Capital A/C 50%').update(opening_balance=500000)
        Ledger.objects.filter(name='Cash-in-hand').update(opening_balance=100000)
        Ledger.objects.filter(name='Bank Account (Main)').update(opening_balance=900000)
        SalesInvoice.objects.create(
            id='INV1', invoice_number='INV1', invoice_date=IN_FY, due_date=IN_FY, customer_id='C1', customer_name='Namkeen Co',
            taxable_amount=100000, cgst_amount=9000, sgst_amount=9000, grand_total=118000, status='Posted')
        PurchaseInvoice.objects.create(
            id='PB1', invoice_number='PB1', invoice_date=IN_FY, due_date=IN_FY, supplier_id='S1', supplier_name='Steel Traders',
            taxable_amount=40000, igst_amount=7200, grand_total=47200, outstanding_amount=47200, status='Posted', grn_number='')
        CustomerReceipt.objects.create(id='R1', receipt_number='R1', receipt_date=IN_FY, customer_id='C1', customer_name='Namkeen Co',
                                       amount=50000, payment_mode='Bank Transfer', status='Received')
        ExpenseEntry.objects.create(id='E1', expense_number='E1', expense_date=IN_FY, category='Electric Bill', sub_total=2000,
                                    tax_amount=0, grand_total=2000, payment_mode='Cash', status='Approved')

    def test_double_entry_and_statements(self):
        self._book()
        tb = reports.trial_balance()
        self.assertTrue(tb['is_balanced'], tb['difference'])
        self.assertEqual(tb['total_dr'], tb['total_cr'])

        StockItem.objects.filter(name='SS PLATE').update(closing_qty=10)
        s = StockItem.objects.get(name='SS PLATE'); s.rate = 1000; s.save()   # 10,000 closing stock

        pl = reports.profit_loss()
        self.assertEqual(pl['summary']['sales'], 100000.0)
        # GP = sales 100000 + closing 10000 - purchase 40000 - direct exp 2000
        self.assertEqual(pl['summary']['gross_profit'], 68000.0)
        self.assertEqual(pl['summary']['nett_profit'], 68000.0)

        bs = reports.balance_sheet()
        self.assertTrue(bs['is_balanced'], bs['liabilities']['difference_in_books'])
        self.assertEqual(bs['liabilities']['total'], bs['assets']['total'])
        # debtors = 118000 - 50000
        debtors = next(g for g in bs['assets']['current_assets']['groups'] if g['name'] == 'Sundry Debtors')
        self.assertEqual(debtors['total'], 68000.0)

        ra = reports.ratio_analysis()
        cr = next(r for r in ra['ratios'] if r['key'] == 'current_ratio')
        self.assertIsNotNone(cr['value'])
        self.assertEqual(len(ra['ratios']), 11)

    def test_repost_is_idempotent_and_delete_unposts(self):
        self._book()
        n = LedgerEntry.objects.filter(source_type='SalesInvoice').count()
        inv = SalesInvoice.objects.get(pk='INV1'); inv.save(); inv.save()
        self.assertEqual(LedgerEntry.objects.filter(source_type='SalesInvoice').count(), n)
        inv.delete()
        self.assertEqual(LedgerEntry.objects.filter(source_type='SalesInvoice').count(), 0)

    def test_draft_invoice_not_posted(self):
        SalesInvoice.objects.create(id='D1', invoice_number='D1', invoice_date=IN_FY, due_date=IN_FY, customer_id='C',
                                    customer_name='X', taxable_amount=10, grand_total=10, status='Draft')
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_manual_voucher_validation_and_posting(self):
        cash = Ledger.objects.get(name='Cash-in-hand'); exp = Ledger.objects.get(name='OFFICE EXPENSES')
        bad = self.client.post('/api/accounting/vouchers/', {'voucher_type': 'Payment', 'voucher_date': str(IN_FY), 'narration': 'x',
                               'lines': [{'ledger_id': exp.pk, 'debit': 100, 'credit': 0}, {'ledger_id': cash.pk, 'debit': 0, 'credit': 90}]}, format='json')
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post('/api/accounting/vouchers/', {'voucher_type': 'Payment', 'voucher_date': str(IN_FY), 'narration': 'pens',
                              'lines': [{'ledger_id': exp.pk, 'debit': 100, 'credit': 0}, {'ledger_id': cash.pk, 'debit': 0, 'credit': 100}]}, format='json')
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertEqual(LedgerEntry.objects.filter(source_type='Voucher').count(), 2)
        st = self.client.get(f'/api/accounting/ledgers/{cash.pk}/statement/').data
        self.assertEqual(st['closing_type'], 'Cr')
        self.assertEqual(st['total_credit'], 100.0)

    def test_depreciation_chart_and_posting(self):
        a = DepreciationAsset.objects.get(particulars='Machinery', financial_year=posting.current_fy_code())
        a.opening, a.addition1, a.addition2, a.sales = 100000, 50000, 20000, 10000
        a.save()
        c = a.compute()
        # (100000+50000-10000)*15% + 20000*7.5% = 21000 + 1500
        self.assertEqual(c['depreciation'], Decimal('22500.00'))
        self.assertEqual(c['wdv'], Decimal('160000') - Decimal('22500'))
        Ledger.objects.filter(name='15% BLOCK').update(opening_balance=160000)
        r = self.client.post('/api/accounting/depreciation-assets/post-depreciation/', {}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['amount'], 22500.0)
        pl = reports.profit_loss()
        self.assertEqual(pl['pl']['dr']['indirect_expenses'], 22500.0)
        # re-post idempotent
        self.client.post('/api/accounting/depreciation-assets/post-depreciation/', {}, format='json')
        self.assertEqual(reports.profit_loss()['pl']['dr']['indirect_expenses'], 22500.0)

    def test_payment_request_flow_purchase_to_accounts(self):
        self._book()
        req = PaymentRequest.objects.get(source_ref='PB1')
        self.assertEqual(req.status, 'Pending')
        self.assertEqual(float(req.amount), 47200.0)
        self.assertEqual(self.client.post(f'/api/accounting/payment-requests/{req.pk}/approve/').status_code, 200)
        r = self.client.post(f'/api/accounting/payment-requests/{req.pk}/pay/', {'amount': 20000, 'payment_mode': 'Bank Transfer'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['status'], 'Approved'); self.assertEqual(r.data['paid_amount'], '20000.00')
        r = self.client.post(f'/api/accounting/payment-requests/{req.pk}/pay/', {}, format='json')
        self.assertEqual(r.data['status'], 'Paid'); self.assertEqual(r.data['paid_amount'], '47200.00')
        inv = PurchaseInvoice.objects.get(pk='PB1')
        self.assertEqual(inv.payment_status, 'Paid')
        # supplier ledger squared off
        cred = Ledger.objects.get(name='Steel Traders')
        st = self.client.get(f'/api/accounting/ledgers/{cred.pk}/statement/').data
        self.assertEqual(st['closing'], 0.0)
        self.assertTrue(reports.trial_balance()['is_balanced'])
        # over-payment rejected
        self.assertEqual(self.client.post(f'/api/accounting/payment-requests/{req.pk}/pay/', {'amount': 1}, format='json').status_code, 400)

    def test_grn_creates_request_then_bill_upgrades_it(self):
        from apps.store.models import GoodsReceiptNote
        GoodsReceiptNote.objects.create(id='G1', grn_number='GRN-1', date='2026-01-01', supplier_id='S9', supplier_name='Bolt Co',
                                        received_by='Store', grand_total=5000, status='Accepted', qc_status='Pass', po_number='PO-9')
        req = PaymentRequest.objects.get(source_ref='GRN-1')
        self.assertEqual(req.department, 'Store'); self.assertEqual(float(req.amount), 5000.0)
        PurchaseInvoice.objects.create(id='PB9', invoice_number='PB9', invoice_date=IN_FY, due_date=IN_FY, supplier_id='S9',
                                       supplier_name='Bolt Co', taxable_amount=5000, grand_total=5000, outstanding_amount=5000,
                                       status='Posted', grn_number='GRN-1', po_number='PO-9')
        self.assertEqual(PaymentRequest.objects.filter(supplier_name='Bolt Co').count(), 1)
        self.assertEqual(PaymentRequest.objects.get(supplier_name='Bolt Co').source_type, 'Purchase Invoice')

    def test_report_endpoints_and_rebuild(self):
        self._book()
        for k in ('trial-balance', 'profit-loss', 'balance-sheet', 'ratio-analysis'):
            self.assertEqual(self.client.get(f'/api/accounting/reports/{k}/').status_code, 200, k)
        r = self.client.post('/api/accounting/setup/rebuild/')
        self.assertEqual(r.status_code, 200); self.assertEqual(r.data['errors'], [])
        self.assertTrue(reports.trial_balance()['is_balanced'])
        self.assertEqual(self.client.get('/api/accounting/day-book/').status_code, 200)
