from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
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



