from datetime import datetime, date, timedelta
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    FinancialYear, ChartOfAccount, TaxMaster, CostCenter,
    SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment,
    JournalEntry, JobCostingSummary, CreditNote, DebitNote,
    BankAccount, ContraVoucher, ExpenseEntry, FixedAsset
)
from .serializers import (
    FinancialYearSerializer, ChartOfAccountSerializer, TaxMasterSerializer,
    CostCenterSerializer, SalesInvoiceSerializer, PurchaseInvoiceSerializer,
    CustomerReceiptSerializer, SupplierPaymentSerializer, JournalEntrySerializer,
    JobCostingSummarySerializer, CreditNoteSerializer, DebitNoteSerializer,
    BankAccountSerializer, ContraVoucherSerializer, ExpenseEntrySerializer, FixedAssetSerializer
)


class FinancialYearViewSet(viewsets.ModelViewSet):
    queryset = FinancialYear.objects.all()
    serializer_class = FinancialYearSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['name', 'fy_code']
    filterset_fields = ['status']


class ChartOfAccountViewSet(viewsets.ModelViewSet):
    queryset = ChartOfAccount.objects.all()
    serializer_class = ChartOfAccountSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['account_code', 'account_name']
    filterset_fields = ['category', 'account_type', 'status']


class TaxMasterViewSet(viewsets.ModelViewSet):
    queryset = TaxMaster.objects.all()
    serializer_class = TaxMasterSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['tax_code', 'tax_name']
    filterset_fields = ['status', 'tax_type']


class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['cost_center_code', 'cost_center_name', 'department']
    filterset_fields = ['status']


class SalesInvoiceViewSet(viewsets.ModelViewSet):
    queryset = SalesInvoice.objects.all()
    serializer_class = SalesInvoiceSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['invoice_number', 'customer_name', 'job_number', 'sales_order_number']
    filterset_fields = ['status', 'payment_status', 'customer_id']

    def create(self, request, *args, **kwargs):
        import threading
        if not hasattr(self.__class__, '_create_lock'):
            self.__class__._create_lock = threading.Lock()

        with self.__class__._create_lock:
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            if not data.get('id') and not data.get('invoice_number') and not data.get('invoiceNumber'):
                count = SalesInvoice.objects.count() + 1
                code = f"INV-2026-{count:04d}"
                while SalesInvoice.objects.filter(Q(id=code) | Q(invoice_number=code)).exists():
                    count += 1
                    code = f"INV-2026-{count:04d}"
                data['id'] = code
                data['invoice_number'] = code
            elif not data.get('id'):
                data['id'] = data.get('invoice_number') or data.get('invoiceNumber')
            if 'invoice_number' not in data:
                data['invoice_number'] = data.get('invoiceNumber') or data.get('id')
        if 'invoice_date' not in data:
            data['invoice_date'] = data.get('invoiceDate') or timezone.now().strftime('%Y-%m-%d')
        if 'due_date' not in data:
            data['due_date'] = data.get('dueDate') or data['invoice_date']
        if 'customer_id' not in data:
            data['customer_id'] = data.get('customerId') or 'CUST-001'
        if 'customer_name' not in data:
            data['customer_name'] = data.get('customerName') or 'Customer'
        if 'taxable_amount' not in data:
            data['taxable_amount'] = data.get('taxableAmount') or data.get('subTotal') or data.get('sub_total') or 0.0
        if 'cgst_amount' not in data:
            data['cgst_amount'] = data.get('cgstAmount') or 0.0
        if 'sgst_amount' not in data:
            data['sgst_amount'] = data.get('sgstAmount') or 0.0
        if 'igst_amount' not in data:
            data['igst_amount'] = data.get('igstAmount') or 0.0
        if 'grand_total' not in data:
            data['grand_total'] = data.get('grandTotal') or data.get('total') or 0.0
        if 'items' not in data:
            data['items'] = []

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment(self, request, pk=None):
        inv = self.get_object()
        amount_paid = float(request.data.get('amount') or request.data.get('amount_paid') or request.data.get('amountPaid') or 0.0)
        mode = request.data.get('payment_mode') or request.data.get('paymentMode') or 'Bank Transfer'
        ref = request.data.get('reference_number') or request.data.get('referenceNumber') or f"PAY-{timezone.now().strftime('%Y%m%d%H%M')}"
        
        inv.paid_amount = float(inv.paid_amount or 0.0) + amount_paid
        inv.outstanding_amount = max(0.0, float(inv.grand_total) - inv.paid_amount)
        if inv.outstanding_amount == 0.0:
            inv.payment_status = 'Paid'
            inv.status = 'Paid'
        else:
            inv.payment_status = 'Partially Paid'
            inv.status = 'Partially Paid'
        inv.save()

        # Auto create CustomerReceipt
        receipt_no = f"REC-{timezone.now().strftime('%Y%m%d')}-{CustomerReceipt.objects.count() + 1:03d}"
        receipt = CustomerReceipt.objects.create(
            id=receipt_no,
            receipt_number=receipt_no,
            receipt_date=timezone.now().date(),
            customer_id=inv.customer_id,
            customer_name=inv.customer_name,
            sales_invoice_number=inv.invoice_number,
            payment_mode=mode,
            bank_name=request.data.get('bank_name') or request.data.get('bankName', 'HDFC Bank Corporate A/c'),
            amount=amount_paid,
            reference_number=ref,
            status='Received',
            created_by=request.data.get('created_by') or 'Finance Dept'
        )

        return Response({
            'invoice': SalesInvoiceSerializer(inv).data,
            'receipt': CustomerReceiptSerializer(receipt).data
        })

    @action(detail=True, methods=['post'], url_path='post')
    def post_invoice(self, request, pk=None):
        inv = self.get_object()
        inv.status = 'Posted'
        inv.save()
        return Response(SalesInvoiceSerializer(inv).data)


class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    queryset = PurchaseInvoice.objects.all()
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['invoice_number', 'supplier_name', 'po_number', 'grn_number']
    filterset_fields = ['status', 'payment_status', 'supplier_id']

    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment(self, request, pk=None):
        inv = self.get_object()
        amount_paid = float(request.data.get('amount') or request.data.get('amount_paid') or request.data.get('amountPaid') or 0.0)
        mode = request.data.get('payment_mode') or request.data.get('paymentMode') or 'Bank Transfer'
        ref = request.data.get('reference_number') or request.data.get('referenceNumber') or f"PAY-{timezone.now().strftime('%Y%m%d%H%M')}"
        
        inv.paid_amount = float(inv.paid_amount or 0.0) + amount_paid
        inv.outstanding_amount = max(0.0, float(inv.grand_total) - inv.paid_amount)
        if inv.outstanding_amount == 0.0:
            inv.payment_status = 'Paid'
            inv.status = 'Paid'
        else:
            inv.payment_status = 'Partially Paid'
            inv.status = 'Partially Paid'
        inv.save()

        # Auto create SupplierPayment
        pay_no = f"PAY-SUP-{timezone.now().strftime('%Y%m%d')}-{SupplierPayment.objects.count() + 1:03d}"
        payment = SupplierPayment.objects.create(
            id=pay_no,
            payment_number=pay_no,
            payment_date=timezone.now().date(),
            supplier_id=inv.supplier_id,
            supplier_name=inv.supplier_name,
            purchase_invoice_number=inv.invoice_number,
            payment_mode=mode,
            bank_name=request.data.get('bank_name') or request.data.get('bankName', 'State Bank of India'),
            amount=amount_paid,
            reference_number=ref,
            status='Paid',
            created_by=request.data.get('created_by') or 'Accounts Dept'
        )

        return Response({
            'invoice': PurchaseInvoiceSerializer(inv).data,
            'payment': SupplierPaymentSerializer(payment).data
        })


class CustomerReceiptViewSet(viewsets.ModelViewSet):
    queryset = CustomerReceipt.objects.all()
    serializer_class = CustomerReceiptSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['receipt_number', 'customer_name', 'sales_invoice_number']
    filterset_fields = ['customer_id', 'status']


class SupplierPaymentViewSet(viewsets.ModelViewSet):
    queryset = SupplierPayment.objects.all()
    serializer_class = SupplierPaymentSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['payment_number', 'supplier_name', 'purchase_invoice_number']
    filterset_fields = ['supplier_id', 'status']


class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['journal_number', 'narration']
    filterset_fields = ['voucher_type', 'status']


class JobCostingSummaryViewSet(viewsets.ModelViewSet):
    queryset = JobCostingSummary.objects.all()
    serializer_class = JobCostingSummarySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['job_number', 'product_name', 'customer_name']


class CreditNoteViewSet(viewsets.ModelViewSet):
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['credit_note_number', 'customer_name', 'original_invoice_number']
    filterset_fields = ['customer_id', 'status']


class DebitNoteViewSet(viewsets.ModelViewSet):
    queryset = DebitNote.objects.all()
    serializer_class = DebitNoteSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['debit_note_number', 'supplier_name', 'original_invoice_number']
    filterset_fields = ['supplier_id', 'status']


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['bank_name', 'account_name', 'account_number', 'ifsc_code']
    filterset_fields = ['account_type', 'status', 'is_active']

    def perform_create(self, serializer):
        req_id = serializer.validated_data.get('id') or self.request.data.get('id')
        if not req_id:
            count = BankAccount.objects.count() + 1
            req_id = f"BANK-{count:02d}"

        opening = serializer.validated_data.get('opening_balance', 0)
        current = serializer.validated_data.get('current_balance', opening)
        acc_name = serializer.validated_data.get('account_name') or serializer.validated_data.get('bank_name', '')

        serializer.save(
            id=req_id,
            account_name=acc_name,
            opening_balance=opening,
            current_balance=current,
        )


class ContraVoucherViewSet(viewsets.ModelViewSet):
    queryset = ContraVoucher.objects.all()
    serializer_class = ContraVoucherSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['contra_number', 'from_account_name', 'to_account_name', 'reference_number', 'narration']
    filterset_fields = ['contra_type', 'status']


class ExpenseEntryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseEntry.objects.all()
    serializer_class = ExpenseEntrySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['expense_number', 'category', 'claimed_by', 'vendor_name', 'description']
    filterset_fields = ['category', 'status', 'payment_mode']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_expense(self, request, pk=None):
        expense = self.get_object()
        expense.status = 'Approved'
        expense.approved_by = request.data.get('approved_by') or request.data.get('approvedBy') or 'Super Admin'
        expense.save()
        return Response(ExpenseEntrySerializer(expense).data)


class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['asset_code', 'asset_name', 'category', 'location']
    filterset_fields = ['category', 'status', 'depreciation_method']


class AccountingDashboardMetricsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        today = timezone.now().date()

        month_keys = []
        month_map = {}
        for i in range(5, -1, -1):
            m = (today.month - i - 1) % 12 + 1
            y = today.year + ((today.month - i - 1) // 12)
            name = date(y, m, 1).strftime('%b')
            key = f"{y}-{m:02d}"
            month_keys.append((key, name))
            month_map[key] = {
                'month': name,
                'Revenue': 0.0,
                'Expense': 0.0,
                'Profit': 0.0,
                'Inflow': 0.0,
                'Outflow': 0.0,
                'NetBalance': 0.0,
            }

        sales_invoices = list(SalesInvoice.objects.all())
        for inv in sales_invoices:
            if inv.invoice_date:
                key = f"{inv.invoice_date.year}-{inv.invoice_date.month:02d}"
                if key in month_map:
                    month_map[key]['Revenue'] += float(inv.grand_total or 0.0)

        purchase_invoices = list(PurchaseInvoice.objects.all())
        for inv in purchase_invoices:
            if inv.invoice_date:
                key = f"{inv.invoice_date.year}-{inv.invoice_date.month:02d}"
                if key in month_map:
                    month_map[key]['Expense'] += float(inv.grand_total or 0.0)

        expense_entries = list(ExpenseEntry.objects.all())
        for exp in expense_entries:
            if exp.expense_date:
                key = f"{exp.expense_date.year}-{exp.expense_date.month:02d}"
                if key in month_map:
                    month_map[key]['Expense'] += float(exp.amount or 0.0)

        receipts = list(CustomerReceipt.objects.all())
        for r in receipts:
            if r.receipt_date:
                key = f"{r.receipt_date.year}-{r.receipt_date.month:02d}"
                if key in month_map:
                    month_map[key]['Inflow'] += float(r.amount or 0.0)

        payments = list(SupplierPayment.objects.all())
        for p in payments:
            if p.payment_date:
                key = f"{p.payment_date.year}-{p.payment_date.month:02d}"
                if key in month_map:
                    month_map[key]['Outflow'] += float(p.amount or 0.0)

        monthly_revenue_expense = []
        cash_flow = []
        for key, name in month_keys:
            data = month_map[key]
            data['Profit'] = data['Revenue'] - data['Expense']
            data['NetBalance'] = data['Inflow'] - data['Outflow']
            monthly_revenue_expense.append({
                'month': data['month'],
                'Revenue': round(data['Revenue'], 2),
                'Expense': round(data['Expense'], 2),
                'Profit': round(data['Profit'], 2),
            })
            cash_flow.append({
                'month': data['month'],
                'Inflow': round(data['Inflow'], 2),
                'Outflow': round(data['Outflow'], 2),
                'NetBalance': round(data['NetBalance'], 2),
            })

        ar_buckets = {'0-30 Days': 0.0, '31-60 Days': 0.0, '61-90 Days': 0.0, '90+ Days': 0.0}
        for inv in sales_invoices:
            outstanding = float(inv.outstanding_amount or (inv.grand_total - inv.paid_amount) or 0.0)
            if outstanding > 0 and inv.invoice_date:
                age = (today - inv.invoice_date).days
                if age <= 30:
                    ar_buckets['0-30 Days'] += outstanding
                elif age <= 60:
                    ar_buckets['31-60 Days'] += outstanding
                elif age <= 90:
                    ar_buckets['61-90 Days'] += outstanding
                else:
                    ar_buckets['90+ Days'] += outstanding

        ar_colors = {'0-30 Days': '#10B981', '31-60 Days': '#3B82F6', '61-90 Days': '#F59E0B', '90+ Days': '#EF4444'}
        ar_aging = [
            {'name': k, 'amount': round(v, 2), 'color': ar_colors[k]} for k, v in ar_buckets.items()
        ]

        ap_buckets = {'0-30 Days': 0.0, '31-60 Days': 0.0, '61-90 Days': 0.0, '90+ Days': 0.0}
        for inv in purchase_invoices:
            outstanding = float(inv.outstanding_amount or (inv.grand_total - inv.paid_amount) or 0.0)
            if outstanding > 0 and inv.invoice_date:
                age = (today - inv.invoice_date).days
                if age <= 30:
                    ap_buckets['0-30 Days'] += outstanding
                elif age <= 60:
                    ap_buckets['31-60 Days'] += outstanding
                elif age <= 90:
                    ap_buckets['61-90 Days'] += outstanding
                else:
                    ap_buckets['90+ Days'] += outstanding

        ap_aging = [
            {'name': k, 'amount': round(v, 2), 'color': ar_colors[k]} for k, v in ap_buckets.items()
        ]

        exp_categories = {}
        for exp in expense_entries:
            cat = exp.category or 'General Overhead'
            exp_categories[cat] = exp_categories.get(cat, 0.0) + float(exp.amount or 0.0)

        pi_total = sum(float(inv.taxable_amount or inv.grand_total or 0.0) for inv in purchase_invoices)
        if pi_total > 0:
            exp_categories['Raw Material & Components'] = exp_categories.get('Raw Material & Components', 0.0) + pi_total

        palette = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#E11D48']
        expense_breakdown = [
            {'name': k, 'value': round(v, 2), 'color': palette[idx % len(palette)]}
            for idx, (k, v) in enumerate(exp_categories.items())
        ]

        return Response({
            'monthly_revenue_expense': monthly_revenue_expense,
            'cash_flow': cash_flow,
            'ar_aging': ar_aging,
            'ap_aging': ap_aging,
            'expense_breakdown': expense_breakdown,
            'total_sales_invoices': len(sales_invoices),
            'total_purchase_invoices': len(purchase_invoices),
            'total_receipts': len(receipts),
            'total_payments': len(payments),
        })




