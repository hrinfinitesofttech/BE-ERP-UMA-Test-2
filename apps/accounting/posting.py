"""
Posting engine: converts every accounting document (invoice, receipt, payment, expense, journal...)
into balanced double-entry LedgerEntry rows. Idempotent: re-posting a source replaces its entries.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction

from . import ledger_data as D
from .ledger_models import AccountGroup, Ledger, LedgerEntry, DepreciationAsset, StockItem

log = logging.getLogger(__name__)
ZERO = Decimal('0')
SKIP_STATUSES = {'draft', 'cancelled', 'canceled', 'rejected', 'void'}


def dec(v):
    try:
        return Decimal(str(v or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        return ZERO


# --------------------------------------------------------------------------- master seed
def seed_master():
    """Create the full UMA Techno Fab chart of accounts, depreciation chart and stock list (idempotent)."""
    created = {'groups': 0, 'ledgers': 0, 'assets': 0, 'stock': 0}
    groups = {}
    for name, parent, nature, sort in D.GROUPS:
        g, new = AccountGroup.objects.get_or_create(
            name=name, defaults={'nature': nature, 'sort_order': sort, 'is_system': True,
                                 'parent': groups.get(parent) if parent else None})
        groups[name] = g
        created['groups'] += int(new)
    for gname, (names, otype) in D.LEDGERS.items():
        for i, lname in enumerate(names):
            _, new = Ledger.objects.get_or_create(
                name=lname, defaults={'group': groups[gname], 'opening_type': otype, 'is_system': True, 'sort_order': i})
            created['ledgers'] += int(new)
    for i, (grp, part, rate) in enumerate(D.DEPRECIATION_ASSETS):
        _, new = DepreciationAsset.objects.get_or_create(
            financial_year=current_fy_code(), particulars=part,
            defaults={'group_name': grp, 'rate': rate, 'sort_order': i})
        created['assets'] += int(new)
    n = 0
    for name in D.FINISHED_GOODS:
        _, new = StockItem.objects.get_or_create(name=name, defaults={'category': 'Finished Goods', 'sort_order': n})
        created['stock'] += int(new); n += 1
    for sub, names in D.RAW_MATERIAL.items():
        for name in names:
            _, new = StockItem.objects.get_or_create(
                name=name, defaults={'category': 'Raw Material', 'sub_group': sub, 'sort_order': n})
            created['stock'] += int(new); n += 1
    return created


def current_fy_code(today=None):
    from datetime import date
    today = today or date.today()
    y = today.year if today.month >= 4 else today.year - 1
    return f"{y}-{str(y + 1)[2:]}"


# --------------------------------------------------------------------------- ledger helpers
def get_ledger(name, group_name, opening_type=None, **extra):
    name = (name or '').strip()[:255]
    led = Ledger.objects.filter(name__iexact=name).first()
    if led:
        return led
    group = AccountGroup.objects.filter(name=group_name).first()
    if not group:
        seed_master()
        led = Ledger.objects.filter(name__iexact=name).first()
        if led:
            return led
        group = AccountGroup.objects.get(name=group_name)
    otype = opening_type or ('Cr' if group.nature in D_CREDIT else 'Dr')
    try:
        with transaction.atomic():
            return Ledger.objects.create(name=name, group=group, opening_type=otype, **extra)
    except IntegrityError:
        return Ledger.objects.get(name__iexact=name)


D_CREDIT = {'Capital', 'Loans', 'CurrentLiabilities', 'Sales', 'DirectIncome', 'IndirectIncome'}


def party_ledger(kind, party_id, name):
    group = 'Sundry Debtors' if kind == 'customer' else 'Sundry Creditors'
    name = (name or ('Customer' if kind == 'customer' else 'Supplier')).strip()
    return get_ledger(name, group, party_type=kind, party_id=str(party_id or ''))


def bank_cash_ledger(mode='', name=''):
    mode = (mode or '').lower()
    if 'cash' in mode and 'bank' not in mode:
        return get_ledger('Cash-in-hand', 'Cash-in-hand')
    name = (name or '').strip()
    if name:
        return get_ledger(name, 'Bank Accounts', party_type='bank')
    return get_ledger('Bank Account (Main)', 'Bank Accounts')


def tax_ledgers(cgst, sgst, igst, kind):
    """kind = Output | Input -> list of (ledger, amount)"""
    out = []
    for lbl, amt in (('CGST', cgst), ('SGST', sgst), ('IGST', igst)):
        if dec(amt) > 0:
            out.append((get_ledger(f'{lbl} {kind}', 'Duties & Taxes'), dec(amt)))
    return out


# --------------------------------------------------------------------------- core poster
def post_lines(source_type, source_id, voucher_type, voucher_no, voucher_date, lines, narration=''):
    """lines: list of (ledger, debit, credit[, narration]). Replaces earlier postings of the same source."""
    with transaction.atomic():
        LedgerEntry.objects.filter(source_type=source_type, source_id=str(source_id)).delete()
        rows = []
        for ln in lines:
            led, d, c = ln[0], dec(ln[1]), dec(ln[2])
            if d == 0 and c == 0:
                continue
            rows.append([led, d, c, ln[3] if len(ln) > 3 and ln[3] else narration])
        diff = sum(r[1] for r in rows) - sum(r[2] for r in rows)
        if diff != 0 and rows:
            fix = get_ledger('Round Off', 'Indirect Incomes') if abs(diff) < 1 else get_ledger('Suspance A/c', 'Current Liabilities')
            rows.append([fix, ZERO if diff > 0 else -diff, diff if diff > 0 else ZERO, 'Auto balancing difference'])
            if abs(diff) >= 1:
                log.warning('Unbalanced voucher %s (diff %s) pushed to Suspense', voucher_no, diff)
        LedgerEntry.objects.bulk_create([
            LedgerEntry(voucher_type=voucher_type, voucher_no=voucher_no, voucher_date=voucher_date, ledger=r[0],
                        debit=r[1], credit=r[2], narration=r[3] or '', source_type=source_type, source_id=str(source_id))
            for r in rows])


def unpost(source_type, source_id):
    LedgerEntry.objects.filter(source_type=source_type, source_id=str(source_id)).delete()


def _skip(status):
    return (status or '').strip().lower() in SKIP_STATUSES


# --------------------------------------------------------------------------- document rules
def post_sales_invoice(inv):
    if _skip(inv.status):
        return unpost('SalesInvoice', inv.pk)
    taxable = dec(inv.taxable_amount or inv.subtotal)
    cg, sg, ig = dec(inv.cgst_amount or inv.cgst_total), dec(inv.sgst_amount or inv.sgst_total), dec(inv.igst_amount or inv.igst_total)
    total = dec(inv.grand_total)
    sales = get_ledger('SALES INVOICE (OGS)' if ig > 0 else 'SALES GST @ 18%', 'Sales Accounts')
    lines = [(party_ledger('customer', inv.customer_id, inv.customer_name), total, 0)]
    lines.append((sales, 0, taxable))
    lines += [(l, 0, a) for l, a in tax_ledgers(cg, sg, ig, 'Output')]
    post_lines('SalesInvoice', inv.pk, 'Sales', inv.invoice_number, inv.invoice_date, lines,
               f'Sales to {inv.customer_name} Inv {inv.invoice_number}')


def post_purchase_invoice(inv):
    if _skip(inv.status):
        return unpost('PurchaseInvoice', inv.pk)
    taxable = dec(inv.taxable_amount)
    cg, sg, ig = dec(inv.cgst_amount), dec(inv.sgst_amount), dec(inv.igst_amount)
    total = dec(inv.grand_total)
    purch = get_ledger('Purchase - GST (OGS)' if ig > 0 else 'Purchase- GST Local', 'Purchase Accounts')
    lines = [(purch, taxable, 0)]
    lines += [(l, a, 0) for l, a in tax_ledgers(cg, sg, ig, 'Input')]
    lines.append((party_ledger('supplier', inv.supplier_id, inv.supplier_name), 0, total))
    post_lines('PurchaseInvoice', inv.pk, 'Purchase', inv.invoice_number, inv.invoice_date, lines,
               f'Purchase from {inv.supplier_name} Bill {inv.vendor_invoice_number or inv.invoice_number}')


def post_customer_receipt(r):
    if _skip(r.status):
        return unpost('CustomerReceipt', r.pk)
    amt = dec(r.amount or r.amount_paid)
    tds = dec(r.tds_deducted_by_customer)
    bank = bank_cash_ledger(r.payment_mode, r.bank_cash_account_name or r.bank_name)
    lines = [(bank, amt, 0)]
    if tds > 0:
        lines.append((get_ledger('TDS Receivable', 'Tax Receivables'), tds, 0))
    lines.append((party_ledger('customer', r.customer_id, r.customer_name), 0, amt + tds))
    post_lines('CustomerReceipt', r.pk, 'Receipt', r.receipt_number, r.receipt_date or r.date, lines,
               f'Receipt from {r.customer_name} {r.reference_number}')


def post_supplier_payment(p):
    if _skip(p.status):
        return unpost('SupplierPayment', p.pk)
    amt = dec(p.amount)
    lines = [(party_ledger('supplier', p.supplier_id, p.supplier_name), amt, 0),
             (bank_cash_ledger(p.payment_mode, p.bank_name), 0, amt)]
    post_lines('SupplierPayment', p.pk, 'Payment', p.payment_number, p.payment_date, lines,
               f'Payment to {p.supplier_name} {p.reference_number}')


def post_expense(e):
    if (e.status or '').lower() not in ('approved', 'paid', 'posted'):
        return unpost('ExpenseEntry', e.pk)
    base, tax, total = dec(e.sub_total), dec(e.tax_amount), dec(e.grand_total)
    if total == 0:
        total = base + tax
    if base == 0:
        base = total - tax
    exp = get_ledger(e.category or 'Mics. Exp.', 'Indirect Expenses')
    lines = [(exp, base, 0)]
    if tax > 0:
        half = (tax / 2).quantize(Decimal('0.01'))
        lines += [(get_ledger('CGST Input', 'Duties & Taxes'), half, 0), (get_ledger('SGST Input', 'Duties & Taxes'), tax - half, 0)]
    lines.append((bank_cash_ledger(e.payment_mode, e.bank_cash_account_name), 0, total))
    post_lines('ExpenseEntry', e.pk, 'Payment', e.expense_number, e.expense_date, lines, e.description or f'{e.category} expense')


def _resolve_line_ledger(l):
    from .models import ChartOfAccount
    name = l.get('accountName') or l.get('account_name') or l.get('ledger_name') or l.get('ledger')
    if name:
        led = Ledger.objects.filter(name__iexact=str(name).strip()).first()
        if led:
            return led
    lid = l.get('ledger_id') or l.get('ledgerId')
    if lid and str(lid).isdigit():
        led = Ledger.objects.filter(pk=int(lid)).first()
        if led:
            return led
    ref = l.get('accountId') or l.get('account_id') or l.get('accountCode') or l.get('account_code')
    if ref:
        coa = ChartOfAccount.objects.filter(id=ref).first() or ChartOfAccount.objects.filter(account_code=ref).first()
        if coa:
            led = Ledger.objects.filter(name__iexact=coa.account_name).first()
            if led:
                return led
    return get_ledger('Suspance A/c', 'Current Liabilities')


def post_journal_entry(j):
    if _skip(j.status):
        return unpost('JournalEntry', j.pk)
    lines = []
    for l in (j.lines or []):
        lines.append((_resolve_line_ledger(l), dec(l.get('debitAmount', l.get('debit'))), dec(l.get('creditAmount', l.get('credit'))),
                      l.get('narration')))
    post_lines('JournalEntry', j.pk, j.voucher_type or 'Journal', j.journal_number, j.journal_date, lines, j.narration)


def post_contra(c):
    if _skip(c.status):
        return unpost('ContraVoucher', c.pk)
    amt = dec(c.amount)

    def led(name, code):
        n = (name or code or '').strip()
        return bank_cash_ledger('cash' if n.lower().startswith('cash') else 'bank', n)
    lines = [(led(c.to_account_name, c.to_account_code), amt, 0), (led(c.from_account_name, c.from_account_code), 0, amt)]
    post_lines('ContraVoucher', c.pk, 'Contra', c.contra_number, c.contra_date, lines, c.narration)


def post_credit_note(n):
    if _skip(n.status):
        return unpost('CreditNote', n.pk)
    taxable, tax, total = dec(n.taxable_amount), dec(n.tax_amount), dec(n.total_amount)
    half = (tax / 2).quantize(Decimal('0.01'))
    lines = [(get_ledger('SALES GST @ 18%', 'Sales Accounts'), taxable, 0)]
    if tax > 0:
        lines += [(get_ledger('CGST Output', 'Duties & Taxes'), half, 0), (get_ledger('SGST Output', 'Duties & Taxes'), tax - half, 0)]
    lines.append((party_ledger('customer', n.customer_id, n.customer_name), 0, total))
    post_lines('CreditNote', n.pk, 'Credit Note', n.credit_note_number, n.credit_note_date, lines, n.reason)


def post_debit_note(n):
    if _skip(n.status):
        return unpost('DebitNote', n.pk)
    taxable, tax, total = dec(n.taxable_amount), dec(n.tax_amount), dec(n.total_amount)
    half = (tax / 2).quantize(Decimal('0.01'))
    lines = [(party_ledger('supplier', n.supplier_id, n.supplier_name), total, 0),
             (get_ledger('Purchase- GST Local', 'Purchase Accounts'), 0, taxable)]
    if tax > 0:
        lines += [(get_ledger('CGST Input', 'Duties & Taxes'), 0, half), (get_ledger('SGST Input', 'Duties & Taxes'), 0, tax - half)]
    post_lines('DebitNote', n.pk, 'Debit Note', n.debit_note_number, n.debit_note_date, lines, n.reason)


def post_voucher(v):
    if _skip(v.status):
        return unpost('Voucher', v.pk)
    lines = []
    for l in (v.lines or []):
        lines.append((_resolve_line_ledger(l), dec(l.get('debit')), dec(l.get('credit')), l.get('narration')))
    post_lines('Voucher', v.pk, v.voucher_type, v.voucher_no, v.voucher_date, lines, v.narration)


# --------------------------------------------------------------------------- depreciation journal
def post_depreciation(fy, voucher_date=None):
    """Post the year's depreciation: Dr DEPRECIATION, Cr each block ledger."""
    from datetime import date
    from .ledger_models import Voucher
    totals = {}
    for a in DepreciationAsset.objects.filter(financial_year=fy):
        dep = a.compute()['depreciation']
        if dep > 0:
            totals[a.group_name] = totals.get(a.group_name, ZERO) + dep
    if not totals:
        Voucher.objects.filter(voucher_no=f'DEP-{fy}').delete()
        return ZERO
    y = int(fy[:4]) + 1
    vdate = voucher_date or date(y, 3, 31)
    lines = [{'ledger_id': get_ledger('DEPRECIATION', 'Indirect Expenses').pk, 'debit': str(sum(totals.values())), 'credit': '0'}]
    for grp, amt in totals.items():
        lname = D.BLOCK_LEDGER.get(grp, grp)
        lines.append({'ledger_id': get_ledger(lname, 'Fixed Assets').pk, 'debit': '0', 'credit': str(amt)})
    v, _ = Voucher.objects.update_or_create(
        voucher_no=f'DEP-{fy}',
        defaults={'voucher_type': 'Journal', 'voucher_date': vdate, 'narration': f'Depreciation for F.Y. {fy} as per depreciation chart',
                  'lines': lines, 'total_amount': sum(totals.values()), 'status': 'Posted', 'created_by': 'System'})
    return sum(totals.values())


# --------------------------------------------------------------------------- bulk repost
def rebuild_all():
    from . import models as M
    from .ledger_models import Voucher
    LedgerEntry.objects.all().delete()
    pairs = [(M.SalesInvoice, post_sales_invoice), (M.PurchaseInvoice, post_purchase_invoice),
             (M.CustomerReceipt, post_customer_receipt), (M.SupplierPayment, post_supplier_payment),
             (M.ExpenseEntry, post_expense), (M.JournalEntry, post_journal_entry), (M.ContraVoucher, post_contra),
             (M.CreditNote, post_credit_note), (M.DebitNote, post_debit_note), (Voucher, post_voucher)]
    counts, errors = {}, []
    for model, fn in pairs:
        n = 0
        for obj in model.objects.all():
            try:
                fn(obj); n += 1
            except Exception as ex:  # keep going, report
                errors.append(f'{model.__name__} {obj.pk}: {ex}')
        counts[model.__name__] = n
    return {'posted': counts, 'errors': errors[:20]}
