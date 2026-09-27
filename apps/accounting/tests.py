from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from .models import SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment, JobCostingSummary


class AccountingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_sales_invoice_and_record_payment(self):
        inv = SalesInvoice.objects.create(
            id='INV-TEST-001',
            invoice_number='INV-TEST-001',
            invoice_date=date(2026, 9, 1),
            due_date=date(2026, 9, 30),
            customer_id='CUST-001',
            customer_name='Reliance Industries',
            taxable_amount=1000000.0,
            grand_total=1180000.0,
            paid_amount=0.0,
            outstanding_amount=1180000.0,
            status='Submitted',
            payment_status='Unpaid'
        )

        res = self.client.post(
            f'/api/sales-invoices/{inv.id}/record-payment/',
            {
                'amount': 500000.0,
                'paymentMode': 'RTGS',
                'referenceNumber': 'UTR-TEST-123456'
            },
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        inv.refresh_from_db()
        self.assertEqual(float(inv.paid_amount), 500000.0)
        self.assertEqual(float(inv.outstanding_amount), 680000.0)
        self.assertEqual(inv.payment_status, 'Partially Paid')

        # Check that customer receipt was auto-created
        receipt = CustomerReceipt.objects.filter(sales_invoice_number=inv.invoice_number).first()
        self.assertIsNotNone(receipt)
        self.assertEqual(float(receipt.amount), 500000.0)

    def test_purchase_invoice_and_record_payment(self):
        pinv = PurchaseInvoice.objects.create(
            id='PINV-TEST-001',
            invoice_number='PINV-TEST-001',
            invoice_date=date(2026, 9, 1),
            due_date=date(2026, 9, 30),
            supplier_id='SUP-001',
            supplier_name='SAIL',
            taxable_amount=500000.0,
            grand_total=590000.0,
            paid_amount=0.0,
            outstanding_amount=590000.0,
            status='Approved',
            payment_status='Unpaid'
        )

        res = self.client.post(
            f'/api/purchase-invoices/{pinv.id}/record-payment/',
            {
                'amount': 590000.0,
                'paymentMode': 'NEFT',
                'referenceNumber': 'NEFT-TEST-9988'
            },
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pinv.refresh_from_db()
        self.assertEqual(float(pinv.paid_amount), 590000.0)
        self.assertEqual(float(pinv.outstanding_amount), 0.0)
        self.assertEqual(pinv.payment_status, 'Paid')

        # Check supplier payment
        pay = SupplierPayment.objects.filter(purchase_invoice_number=pinv.invoice_number).first()
        self.assertIsNotNone(pay)
        self.assertEqual(float(pay.amount), 590000.0)
