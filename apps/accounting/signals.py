"""Auto-posting & cross-department integration signals."""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from . import posting
from .ledger_models import Voucher, PaymentRequest
from .models import (SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment, ExpenseEntry, JournalEntry,
                     ContraVoucher, CreditNote, DebitNote)

log = logging.getLogger(__name__)

POSTERS = {
    SalesInvoice: posting.post_sales_invoice, PurchaseInvoice: posting.post_purchase_invoice,
    CustomerReceipt: posting.post_customer_receipt, SupplierPayment: posting.post_supplier_payment,
    ExpenseEntry: posting.post_expense, JournalEntry: posting.post_journal_entry, ContraVoucher: posting.post_contra,
    CreditNote: posting.post_credit_note, DebitNote: posting.post_debit_note, Voucher: posting.post_voucher,
}


def _make_post(fn):
    def handler(sender, instance, **kwargs):
        if kwargs.get('raw'):
            return
        try:
            with transaction.atomic():
                fn(instance)
        except Exception:  # never block the business save because of accounting
            log.exception('Ledger posting failed for %s %s', sender.__name__, instance.pk)
    return handler


def _make_unpost(model):
    def handler(sender, instance, **kwargs):
        try:
            posting.unpost(model.__name__, instance.pk)
        except Exception:
            log.exception('Ledger unposting failed for %s %s', model.__name__, instance.pk)
    return handler


def _next_request_no():
    n = PaymentRequest.objects.count() + 1
    no = f"PR-{timezone.now().strftime('%y%m')}-{n:04d}"
    while PaymentRequest.objects.filter(request_no=no).exists():
        n += 1
        no = f"PR-{timezone.now().strftime('%y%m')}-{n:04d}"
    return no


def sync_request_from_invoice(inv, **kw):
    """Purchase bill posted -> Accounts gets a payment request (upgrading any open GRN request)."""
    if (inv.status or '').lower() in posting.SKIP_STATUSES:
        return
    outstanding = Decimal(str(inv.outstanding_amount if inv.outstanding_amount is not None else 0))
    total = Decimal(str(inv.grand_total or 0))
    if outstanding == 0 and Decimal(str(inv.paid_amount or 0)) == 0:
        outstanding = total
    req = (PaymentRequest.objects.filter(source_type='Purchase Invoice', source_ref=inv.invoice_number).first()
           or (PaymentRequest.objects.filter(source_type='GRN', source_ref=inv.grn_number, status__in=['Pending', 'Approved']).first()
               if inv.grn_number else None))
    fields = dict(source_type='Purchase Invoice', source_ref=inv.invoice_number, po_number=inv.po_number or '',
                  supplier_id=inv.supplier_id, supplier_name=inv.supplier_name, amount=total,
                  paid_amount=Decimal(str(inv.paid_amount or 0)), due_date=inv.due_date,
                  description=f'Purchase bill {inv.vendor_invoice_number or inv.invoice_number}')
    if req is None:
        req = PaymentRequest(request_no=_next_request_no(), department='Purchase', requested_by=inv.created_by or 'Purchase', status='Pending')
    for k, v in fields.items():
        setattr(req, k, v)
    if (inv.payment_status or '').lower() == 'paid' or (total > 0 and req.paid_amount >= total):
        req.status = 'Paid'
    elif req.status == 'Paid':
        req.status = 'Approved'
    req.save()


def _grn_amount(grn):
    return Decimal(str(grn.grand_total or grn.total_received_value or 0))


def sync_request_from_grn(grn, **kw):
    """Store accepts goods -> Accounts is told a payable is coming (only if no bill exists yet)."""
    if kw.get('raw'):
        return
    if (grn.status or '').lower() not in ('accepted', 'received', 'completed', 'approved'):
        return
    if (grn.qc_status or '').lower() == 'fail':
        return
    amt = _grn_amount(grn)
    if amt <= 0:
        return
    if PurchaseInvoice.objects.filter(grn_number=grn.grn_number).exists():
        return
    req = PaymentRequest.objects.filter(source_type='GRN', source_ref=grn.grn_number).first()
    if req and req.status in ('Paid', 'Rejected'):
        return
    if req is None:
        req = PaymentRequest(request_no=_next_request_no(), source_type='GRN', source_ref=grn.grn_number,
                             department='Store', status='Pending', requested_by=grn.received_by or 'Store')
    req.po_number = grn.po_number or ''
    req.supplier_id = grn.supplier_id
    req.supplier_name = grn.supplier_name
    req.amount = amt
    req.description = f'Goods received (GRN {grn.grn_number}) - bill/payment due'
    req.save()


def connect():
    for model, fn in POSTERS.items():
        uid = f'acc_post_{model.__name__}'
        post_save.connect(_make_post(fn), sender=model, weak=False, dispatch_uid=uid)
        if model is Voucher:
            post_delete.connect(_make_unpost(model), sender=model, weak=False, dispatch_uid=uid + '_del')
        else:
            post_delete.connect(_make_unpost(model), sender=model, weak=False, dispatch_uid=uid + '_del')

    def on_invoice(sender, instance, **kw):
        if kw.get('raw'):
            return
        try:
            with transaction.atomic():
                sync_request_from_invoice(instance)
        except Exception:
            log.exception('PaymentRequest sync failed for invoice %s', instance.pk)
    post_save.connect(on_invoice, sender=PurchaseInvoice, weak=False, dispatch_uid='acc_req_invoice')

    try:
        from apps.store.models import GoodsReceiptNote

        def on_grn(sender, instance, **kw):
            try:
                with transaction.atomic():
                    sync_request_from_grn(instance, **kw)
            except Exception:
                log.exception('PaymentRequest sync failed for GRN %s', instance.pk)
        post_save.connect(on_grn, sender=GoodsReceiptNote, weak=False, dispatch_uid='acc_req_grn')
    except Exception:
        log.exception('GRN integration not connected')
