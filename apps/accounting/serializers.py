from rest_framework import serializers
from .models import (
    FinancialYear, ChartOfAccount, TaxMaster, CostCenter,
    SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment,
    JournalEntry, JobCostingSummary, CreditNote, DebitNote,
    BankAccount, ContraVoucher, ExpenseEntry
)


class FinancialYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialYear
        fields = '__all__'


class ChartOfAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartOfAccount
        fields = '__all__'


class TaxMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxMaster
        fields = '__all__'


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'


class SalesInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoice
        fields = '__all__'


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoice
        fields = '__all__'


class CustomerReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerReceipt
        fields = '__all__'


class SupplierPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPayment
        fields = '__all__'


class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = '__all__'


class JobCostingSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCostingSummary
        fields = '__all__'


class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
        fields = '__all__'


class DebitNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitNote
        fields = '__all__'


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'


class ContraVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContraVoucher
        fields = '__all__'


class ExpenseEntrySerializer(serializers.ModelSerializer):
    expenseNumber = serializers.CharField(source='expense_number', required=False)
    expenseDate = serializers.DateField(source='expense_date', required=False)
    claimedBy = serializers.CharField(source='claimed_by', required=False, allow_blank=True)
    vendorName = serializers.CharField(source='vendor_name', required=False, allow_blank=True)
    subTotal = serializers.DecimalField(source='sub_total', max_digits=16, decimal_places=2, required=False)
    taxAmount = serializers.DecimalField(source='tax_amount', max_digits=16, decimal_places=2, required=False)
    grandTotal = serializers.DecimalField(source='grand_total', max_digits=16, decimal_places=2, required=False)
    paymentMode = serializers.CharField(source='payment_mode', required=False, allow_blank=True)
    bankCashAccountName = serializers.CharField(source='bank_cash_account_name', required=False, allow_blank=True)
    costCenterCode = serializers.CharField(source='cost_center_code', required=False, allow_blank=True)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)
    createdBy = serializers.CharField(source='created_by', required=False, allow_blank=True)

    class Meta:
        model = ExpenseEntry
        fields = '__all__'

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'id' in data:
            ret['id'] = data['id']
        if 'expenseNumber' in data and 'expense_number' not in ret:
            ret['expense_number'] = data['expenseNumber']
        if 'expenseDate' in data and 'expense_date' not in ret:
            ret['expense_date'] = data['expenseDate']
        if 'subTotal' in data and 'sub_total' not in ret:
            ret['sub_total'] = data['subTotal']
        if 'taxAmount' in data and 'tax_amount' not in ret:
            ret['tax_amount'] = data['taxAmount']
        if 'grandTotal' in data and 'grand_total' not in ret:
            ret['grand_total'] = data['grandTotal']
        if 'claimedBy' in data and 'claimed_by' not in ret:
            ret['claimed_by'] = data['claimedBy']
        if 'paymentMode' in data and 'payment_mode' not in ret:
            ret['payment_mode'] = data['paymentMode']
        return ret

