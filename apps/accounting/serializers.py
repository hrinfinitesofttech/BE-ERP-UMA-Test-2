from datetime import datetime, timedelta
from rest_framework import serializers
from .models import (
    FinancialYear, ChartOfAccount, TaxMaster, CostCenter,
    SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment,
    JournalEntry, JobCostingSummary, CreditNote, DebitNote,
    BankAccount, ContraVoucher, ExpenseEntry, FixedAsset
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


from apps.core.base_serializers import UniversalModelSerializerMixin


class SalesInvoiceSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SalesInvoice
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'invoiceNumber': 'invoice_number',
            'invoiceDate': 'invoice_date',
            'dueDate': 'due_date',
            'customerId': 'customer_id',
            'customerCode': 'customer_code',
            'customerName': 'customer_name',
            'customerGstin': 'customer_gstin',
            'billingAddress': 'billing_address',
            'shippingAddress': 'shipping_address',
            'placeOfSupply': 'place_of_supply',
            'salesOrderId': 'sales_order_id',
            'salesOrderNumber': 'sales_order_number',
            'customerPoNumber': 'customer_po_number',
            'projectId': 'project_id',
            'jobNumber': 'job_number',
            'paymentTerms': 'payment_terms',
            'termsAndConditions': 'terms_and_conditions',
            'subTotal': 'taxable_amount',
            'subtotal': 'taxable_amount',
            'taxableAmount': 'taxable_amount',
            'discountTotal': 'discount_total',
            'cgstAmount': 'cgst_amount',
            'sgstAmount': 'sgst_amount',
            'igstAmount': 'igst_amount',
            'cgstTotal': 'cgst_amount',
            'sgstTotal': 'sgst_amount',
            'igstTotal': 'igst_amount',
            'taxTotal': 'tax_total',
            'roundOff': 'round_off',
            'grandTotal': 'grand_total',
            'paidAmount': 'paid_amount',
            'outstandingAmount': 'outstanding_amount',
            'paymentStatus': 'payment_status',
            'createdBy': 'created_by',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if 'subtotal' not in data and 'taxable_amount' in data:
            data['subtotal'] = data['taxable_amount']
        if 'taxable_amount' not in data and 'subtotal' in data:
            data['taxable_amount'] = data['subtotal']
        if 'cgst_total' not in data and 'cgst_amount' in data:
            data['cgst_total'] = data['cgst_amount']
        if 'sgst_total' not in data and 'sgst_amount' in data:
            data['sgst_total'] = data['sgst_amount']
        if 'igst_total' not in data and 'igst_amount' in data:
            data['igst_total'] = data['igst_amount']
        if 'tax_total' not in data:
            data['tax_total'] = float(data.get('cgst_amount') or 0) + float(data.get('sgst_amount') or 0) + float(data.get('igst_amount') or 0)
        if 'customer' in data and 'customer_id' not in data:
            data['customer_id'] = data.pop('customer')
        if 'salesOrder' in data and 'sales_order_id' not in data:
            data['sales_order_id'] = data.pop('salesOrder')
        if not data.get('customer_name') and data.get('customer_id'):
            try:
                from apps.crm.models import Customer
                c = Customer.objects.filter(id=data['customer_id']).first() or Customer.objects.filter(customer_code=data['customer_id']).first()
                if c:
                    data['customer_name'] = c.company_name
                    if not data.get('customer_code'):
                        data['customer_code'] = c.customer_code
            except Exception:
                pass
        if not data.get('customer_name'):
            data['customer_name'] = data.get('customerName') or data.get('company_name') or 'Valued Customer'
        if not data.get('invoice_number'):
            data['invoice_number'] = data.get('id') or f"SINV-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['invoice_number']
        if not data.get('invoice_date'):
            data['invoice_date'] = data.get('date') or datetime.now().date().isoformat()
        if not data.get('due_date'):
            data['due_date'] = (datetime.now().date() + timedelta(days=30)).isoformat()
        if not data.get('grand_total') and data.get('totalAmount'):
            data['grand_total'] = data.get('totalAmount')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['invoiceNumber'] = instance.invoice_number
        ret['invoiceDate'] = str(instance.invoice_date)
        ret['dueDate'] = str(instance.due_date)
        ret['customerId'] = instance.customer_id
        ret['customerCode'] = instance.customer_code
        ret['customerName'] = instance.customer_name
        ret['customerGstin'] = instance.customer_gstin
        ret['billingAddress'] = instance.billing_address
        ret['shippingAddress'] = instance.shipping_address
        ret['placeOfSupply'] = instance.place_of_supply
        ret['salesOrderId'] = instance.sales_order_id
        ret['salesOrderNumber'] = instance.sales_order_number
        ret['customerPoNumber'] = instance.customer_po_number
        ret['projectId'] = instance.project_id
        ret['jobNumber'] = instance.job_number
        ret['paymentTerms'] = instance.payment_terms
        ret['termsAndConditions'] = instance.terms_and_conditions
        ret['taxableAmount'] = float(instance.taxable_amount)
        ret['subtotal'] = float(instance.subtotal or instance.taxable_amount)
        ret['subTotal'] = float(instance.subtotal or instance.taxable_amount)
        ret['discountTotal'] = float(instance.discount_total)
        ret['cgstAmount'] = float(instance.cgst_amount)
        ret['sgstAmount'] = float(instance.sgst_amount)
        ret['igstAmount'] = float(instance.igst_amount)
        ret['cgstTotal'] = float(instance.cgst_total or instance.cgst_amount)
        ret['sgstTotal'] = float(instance.sgst_total or instance.sgst_amount)
        ret['igstTotal'] = float(instance.igst_total or instance.igst_amount)
        ret['taxTotal'] = float(instance.tax_total or (instance.cgst_amount + instance.sgst_amount + instance.igst_amount))
        ret['roundOff'] = float(instance.round_off)
        ret['grandTotal'] = float(instance.grand_total)
        ret['paidAmount'] = float(instance.paid_amount)
        ret['outstandingAmount'] = float(instance.outstanding_amount)
        ret['paymentStatus'] = instance.payment_status
        ret['createdBy'] = instance.created_by
        return ret


class PurchaseInvoiceSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoice
        fields = '__all__'


class CustomerReceiptSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CustomerReceipt
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'receiptNumber': 'receipt_number',
            'receiptDate': 'receipt_date',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'salesInvoiceNumber': 'sales_invoice_number',
            'paymentMode': 'payment_mode',
            'bankName': 'bank_name',
            'bankAccountId': 'bank_account_id',
            'bankCashAccountCode': 'bank_cash_account_code',
            'bankCashAccountName': 'bank_cash_account_name',
            'referenceNumber': 'reference_number',
            'createdBy': 'created_by',
            'tdsDeductedByCustomer': 'tds_deducted_by_customer',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if 'customer' in data and 'customer_id' not in data:
            data['customer_id'] = data.pop('customer')
        if 'invoice' in data and 'sales_invoice_number' not in data:
            data['sales_invoice_number'] = data.pop('invoice')
        if not data.get('customer_name') and data.get('customer_id'):
            try:
                from apps.crm.models import Customer
                c = Customer.objects.filter(id=data['customer_id']).first() or Customer.objects.filter(customer_code=data['customer_id']).first()
                if c:
                    data['customer_name'] = c.company_name
            except Exception:
                pass
        if not data.get('customer_name'):
            data['customer_name'] = data.get('customerName') or data.get('company_name') or 'Valued Customer'
        if not data.get('receipt_number'):
            data['receipt_number'] = data.get('id') or f"RCT-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['receipt_number']
        if not data.get('receipt_date'):
            data['receipt_date'] = data.get('date') or datetime.now().date().isoformat()
        if not data.get('date'):
            data['date'] = data['receipt_date']
        if 'amount' not in data:
            data['amount'] = data.get('amountPaid') or data.get('amountReceived') or data.get('paidAmount') or 0
        if 'amount_paid' not in data:
            data['amount_paid'] = data.get('amount') or 0
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['receiptNumber'] = instance.receipt_number
        ret['receiptDate'] = str(instance.receipt_date)
        ret['date'] = str(instance.date or instance.receipt_date)
        ret['customerId'] = instance.customer_id
        ret['customerName'] = instance.customer_name
        ret['salesInvoiceNumber'] = instance.sales_invoice_number
        ret['paymentMode'] = instance.payment_mode
        ret['bankName'] = instance.bank_name
        ret['bankAccountId'] = instance.bank_account_id
        ret['bankCashAccountCode'] = instance.bank_cash_account_code
        ret['bankCashAccountName'] = instance.bank_cash_account_name
        ret['amount'] = float(instance.amount)
        ret['amountPaid'] = float(instance.amount_paid or instance.amount)
        ret['tdsDeductedByCustomer'] = float(instance.tds_deducted_by_customer)
        ret['allocations'] = instance.allocations or []
        ret['referenceNumber'] = instance.reference_number
        ret['status'] = instance.status
        ret['remarks'] = instance.remarks
        ret['createdBy'] = instance.created_by
        return ret


class SupplierPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPayment
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'paymentNumber': 'payment_number',
            'paymentDate': 'payment_date',
            'supplierId': 'supplier_id',
            'supplierName': 'supplier_name',
            'purchaseInvoiceNumber': 'purchase_invoice_number',
            'paymentMode': 'payment_mode',
            'bankName': 'bank_name',
            'referenceNumber': 'reference_number',
            'createdBy': 'created_by',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('payment_number'):
            data['payment_number'] = data.get('id') or f"PAY-{int(datetime.now().timestamp())}"
        if not data.get('payment_date'):
            data['payment_date'] = data.get('date') or datetime.now().date().isoformat()
        if 'amount' not in data:
            data['amount'] = data.get('amountPaid') or data.get('amount') or 0
        return super().to_internal_value(data)


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
    accountName = serializers.CharField(source='account_name', required=False, allow_blank=True)
    accountType = serializers.CharField(source='account_type', required=False, default='Current')
    bankName = serializers.CharField(source='bank_name', required=False)
    accountNumber = serializers.CharField(source='account_number', required=False)
    ifscCode = serializers.CharField(source='ifsc_code', required=False, allow_blank=True)
    branch = serializers.CharField(required=False, allow_blank=True)
    branchName = serializers.CharField(source='branch_name', required=False, allow_blank=True)
    glAccountCode = serializers.CharField(source='gl_account_code', required=False, allow_blank=True)
    openingBalance = serializers.DecimalField(source='opening_balance', max_digits=16, decimal_places=2, required=False)
    currentBalance = serializers.DecimalField(source='current_balance', max_digits=16, decimal_places=2, required=False)
    isActive = serializers.BooleanField(source='is_active', required=False, default=True)

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


class FixedAssetSerializer(serializers.ModelSerializer):
    assetCode = serializers.CharField(source='asset_code', required=False)
    assetName = serializers.CharField(source='asset_name', required=False)
    purchaseDate = serializers.DateField(source='purchase_date', required=False)
    purchaseCost = serializers.DecimalField(source='purchase_cost', max_digits=16, decimal_places=2, required=False)
    supplierName = serializers.CharField(source='supplier_name', required=False, allow_blank=True)
    invoiceNumber = serializers.CharField(source='invoice_number', required=False, allow_blank=True)
    usefulLifeYears = serializers.IntegerField(source='useful_life_years', required=False)
    depreciationMethod = serializers.CharField(source='depreciation_method', required=False, allow_blank=True)
    depreciationRate = serializers.DecimalField(source='depreciation_rate', max_digits=6, decimal_places=2, required=False)
    residualValue = serializers.DecimalField(source='residual_value', max_digits=16, decimal_places=2, required=False)
    accumulatedDepreciation = serializers.DecimalField(source='accumulated_depreciation', max_digits=16, decimal_places=2, required=False)
    currentBookValue = serializers.DecimalField(source='current_book_value', max_digits=16, decimal_places=2, required=False)

    class Meta:
        model = FixedAsset
        fields = '__all__'

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'id' in data:
            ret['id'] = data['id']
        if 'assetCode' in data and 'asset_code' not in ret:
            ret['asset_code'] = data['assetCode']
        if 'assetName' in data and 'asset_name' not in ret:
            ret['asset_name'] = data['assetName']
        if 'purchaseDate' in data and 'purchase_date' not in ret:
            ret['purchase_date'] = data['purchaseDate']
        if 'purchaseCost' in data and 'purchase_cost' not in ret:
            ret['purchase_cost'] = data['purchaseCost']
        elif 'purchaseValue' in data and 'purchase_cost' not in ret:
            ret['purchase_cost'] = data['purchaseValue']
        if 'supplierName' in data and 'supplier_name' not in ret:
            ret['supplier_name'] = data['supplierName']
        if 'invoiceNumber' in data and 'invoice_number' not in ret:
            ret['invoice_number'] = data['invoiceNumber']
        if 'usefulLifeYears' in data and 'useful_life_years' not in ret:
            ret['useful_life_years'] = data['usefulLifeYears']
        if 'depreciationMethod' in data and 'depreciation_method' not in ret:
            ret['depreciation_method'] = data['depreciationMethod']
        if 'depreciationRate' in data and 'depreciation_rate' not in ret:
            ret['depreciation_rate'] = data['depreciationRate']
        if 'residualValue' in data and 'residual_value' not in ret:
            ret['residual_value'] = data['residualValue']
        if 'accumulatedDepreciation' in data and 'accumulated_depreciation' not in ret:
            ret['accumulated_depreciation'] = data['accumulatedDepreciation']
        if 'currentBookValue' in data and 'current_book_value' not in ret:
            ret['current_book_value'] = data['currentBookValue']
        return ret


