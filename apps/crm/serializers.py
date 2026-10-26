from datetime import datetime
from rest_framework import serializers
from apps.core.base_serializers import UniversalModelSerializerMixin
from .models import (
    Lead,
    Customer,
    Contact,
    Enquiry,
    Opportunity,
    FollowUp,
    SiteVisit,
    Exhibition,
    Quotation,
    CustomerPO,
    SalesOrder,
    Activity,
)


class LeadSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    mobile = serializers.CharField(required=False, allow_blank=True, default='')
    contact_person = serializers.CharField(required=False, allow_blank=True, default='')
    product_name = serializers.CharField(required=False, allow_blank=True, default='')
    expected_delivery = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    next_follow_up_date = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    country = serializers.CharField(required=False, allow_blank=True, default='India')

    class Meta:
        model = Lead
        fields = [
            'id',
            'lead_no',
            'company_name',
            'industry',
            'website',
            'gstin',
            'address',
            'city',
            'state',
            'country',
            'pincode',
            'contact_person',
            'designation',
            'mobile',
            'alt_mobile',
            'email',
            'whatsapp',
            'product_name',
            'machine_type',
            'quantity',
            'capacity',
            'application',
            'requirement_description',
            'expected_delivery',
            'budget',
            'priority',
            'source',
            'exhibition_id',
            'exhibition_name',
            'assigned_sales_person_id',
            'assigned_sales_person_name',
            'status',
            'next_follow_up_date',
            'remarks',
            'created_date',
            'converted_customer_id',
            'converted_enquiry_id',
            'converted_opportunity_id',
            'attachments',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'leadNo': 'lead_no',
            'companyName': 'company_name',
            'contactPerson': 'contact_person',
            'contact_person': 'contact_person',
            'contact': 'contact_person',
            'mobile': 'mobile',
            'mobileNo': 'mobile',
            'mobile_no': 'mobile',
            'mobileNumber': 'mobile',
            'mobile_number': 'mobile',
            'contactMobile': 'mobile',
            'contact_mobile': 'mobile',
            'contactNumber': 'mobile',
            'contact_number': 'mobile',
            'phone': 'mobile',
            'phoneNumber': 'mobile',
            'phone_number': 'mobile',
            'altMobile': 'alt_mobile',
            'alt_mobile': 'alt_mobile',
            'productName': 'product_name',
            'machineType': 'machine_type',
            'requirementDescription': 'requirement_description',
            'expectedDelivery': 'expected_delivery',
            'assignedSalesPersonId': 'assigned_sales_person_id',
            'assignedSalesPersonName': 'assigned_sales_person_name',
            'nextFollowUpDate': 'next_follow_up_date',
            'createdDate': 'created_date',
            'convertedCustomerId': 'converted_customer_id',
            'convertedEnquiryId': 'converted_enquiry_id',
            'convertedOpportunityId': 'converted_opportunity_id',
            'exhibitionId': 'exhibition_id',
            'exhibitionName': 'exhibition_name',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)

        # Resolve mobile from any possible alias
        mob_val = (
            data.get('mobile') or
            data.get('phone') or
            data.get('contactMobile') or
            data.get('contact_mobile') or
            data.get('mobileNo') or
            data.get('mobile_no') or
            data.get('contactNumber') or
            data.get('contact_number') or
            data.get('phoneNumber') or
            data.get('phone_number') or
            ''
        )
        data['mobile'] = str(mob_val).strip()

        # Convert None to empty string for all text fields to avoid DRF null validation errors
        for str_field in [
            'expected_delivery', 'next_follow_up_date', 'remarks', 'address', 'city', 'state',
            'country', 'pincode', 'industry', 'website', 'gstin', 'designation', 'alt_mobile',
            'whatsapp', 'machine_type', 'capacity', 'application', 'requirement_description',
            'exhibition_id', 'exhibition_name', 'assigned_sales_person_id', 'assigned_sales_person_name'
        ]:
            if data.get(str_field) is None:
                data[str_field] = ''
        inst = getattr(self, 'instance', None)
        if inst:
            # During updates (PUT/PATCH), never override user data with dummy defaults!
            # Pop id and lead_no to prevent primary key modification or unique constraint violation
            data.pop('id', None)
            data.pop('lead_no', None)
            data.pop('leadNo', None)
        else:
            if not data.get('product_name'):
                data['product_name'] = data.get('productName') or data.get('notes') or data.get('requirement_description') or 'Industrial Process Equipment'
            if not data.get('lead_no'):
                data['lead_no'] = data.get('leadNumber') or data.get('id') or f"LEAD-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['lead_no']
            if not data.get('created_date'):
                data['created_date'] = datetime.now().date().isoformat()
            if not data.get('country'):
                data['country'] = 'India'
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['leadNo'] = instance.lead_no
        rep['companyName'] = instance.company_name
        rep['contactPerson'] = instance.contact_person
        rep['altMobile'] = instance.alt_mobile
        rep['productName'] = instance.product_name
        rep['machineType'] = instance.machine_type
        rep['requirementDescription'] = instance.requirement_description
        rep['expectedDelivery'] = str(instance.expected_delivery) if instance.expected_delivery else ''
        rep['assignedSalesPersonId'] = instance.assigned_sales_person_id
        rep['assignedSalesPersonName'] = instance.assigned_sales_person_name
        rep['nextFollowUpDate'] = str(instance.next_follow_up_date) if instance.next_follow_up_date else ''
        rep['createdDate'] = str(instance.created_date) if instance.created_date else ''
        rep['convertedCustomerId'] = instance.converted_customer_id
        rep['convertedEnquiryId'] = instance.converted_enquiry_id
        rep['convertedOpportunityId'] = instance.converted_opportunity_id
        rep['exhibitionId'] = instance.exhibition_id
        rep['exhibitionName'] = instance.exhibition_name

        # Auto-heal display values from linked Quotation or Enquiry if lead has dummy/blank values
        try:
            from .models import Quotation, Enquiry
            target_ids = [val for val in [instance.id, instance.lead_no] if val]

            if rep.get('companyName') in ('Valued Customer', '', None):
                q = Quotation.objects.filter(lead_id__in=target_ids).exclude(customer_name__in=['', 'Valued Customer']).order_by('-id').first()
                if q and q.customer_name:
                    rep['companyName'] = q.customer_name
                    if rep.get('contactPerson') in ('', 'Contact Person', 'Contact', None) and q.contact_person:
                        rep['contactPerson'] = q.contact_person
                    if rep.get('productName') in ('', 'Process Equipment', 'Industrial Process Equipment', None) and q.machine_product:
                        rep['productName'] = q.machine_product
                    if (not rep.get('quantity') or rep.get('quantity') == 0) and q.quantity:
                        rep['quantity'] = q.quantity
                else:
                    enq = Enquiry.objects.filter(lead_id__in=target_ids).exclude(customer_name='').order_by('-id').first()
                    if enq and enq.customer_name:
                        rep['companyName'] = enq.customer_name
                        if rep.get('contactPerson') in ('', 'Contact Person', 'Contact', None) and enq.contact_person:
                            rep['contactPerson'] = enq.contact_person

            if rep.get('contactPerson') in ('', 'Contact Person', 'Contact', None):
                q = Quotation.objects.filter(lead_id__in=target_ids).exclude(contact_person__in=['', 'Contact Person', 'Contact']).order_by('-id').first()
                if q and q.contact_person:
                    rep['contactPerson'] = q.contact_person
                else:
                    enq = Enquiry.objects.filter(lead_id__in=target_ids).exclude(contact_person__in=['', 'Contact Person', 'Contact']).order_by('-id').first()
                    if enq and enq.contact_person:
                        rep['contactPerson'] = enq.contact_person
        except Exception:
            pass

        return rep


class ContactSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id',
            'customer_id',
            'customer_name',
            'name',
            'designation',
            'department',
            'email',
            'mobile',
            'whatsapp',
            'is_primary',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'isPrimary': 'is_primary',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('id'):
            data['id'] = f"CONT-{int(datetime.now().timestamp())}"
        if 'phone' in data and not data.get('mobile'):
            data['mobile'] = data.pop('phone')
        if not data.get('mobile'):
            data['mobile'] = ''
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['isPrimary'] = instance.is_primary
        return rep


class CustomerSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)
    mobile = serializers.CharField(required=False, allow_blank=True, default='')
    contact_person = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_code',
            'customer_type',
            'company_name',
            'industry',
            'gstin',
            'pan',
            'tan',
            'msme_number',
            'tax_category',
            'website',
            'contact_person',
            'designation',
            'mobile',
            'email',
            'whatsapp',
            'billing_address',
            'shipping_address',
            'city',
            'state',
            'country',
            'pincode',
            'payment_terms',
            'credit_period_days',
            'credit_limit',
            'currency',
            'category',
            'assigned_sales_person',
            'bank_name',
            'bank_account_no',
            'bank_account_name',
            'bank_ifsc',
            'bank_branch',
            'linked_lead_id',
            'nearest_port_railway',
            'inspection_requirements',
            'special_instructions',
            'status',
            'created_date',
            'contacts',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'contacts' in data:
            self._incoming_contacts = data.pop('contacts')
        else:
            self._incoming_contacts = None

        field_map = {
            'customerCode': 'customer_code',
            'customerType': 'customer_type',
            'companyName': 'company_name',
            'contactPerson': 'contact_person',
            'billingAddress': 'billing_address',
            'shippingAddress': 'shipping_address',
            'paymentTerms': 'payment_terms',
            'creditPeriodDays': 'credit_period_days',
            'creditLimit': 'credit_limit',
            'assignedSalesPerson': 'assigned_sales_person',
            'msmeNumber': 'msme_number',
            'taxCategory': 'tax_category',
            'bankName': 'bank_name',
            'bankAccountNo': 'bank_account_no',
            'bankAccountName': 'bank_account_name',
            'bankIfsc': 'bank_ifsc',
            'bankBranch': 'bank_branch',
            'linkedLeadId': 'linked_lead_id',
            'nearestPortRailway': 'nearest_port_railway',
            'inspectionRequirements': 'inspection_requirements',
            'specialInstructions': 'special_instructions',
            'createdDate': 'created_date',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if 'phone' in data and 'mobile' not in data:
            data['mobile'] = data.pop('phone')
        if 'address' in data and not data.get('billing_address'):
            data['billing_address'] = data.get('address')
        if 'name' in data and not data.get('company_name'):
            data['company_name'] = data.pop('name')

        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('company_name'):
                data['company_name'] = 'Customer Co'
            if not data.get('customer_code'):
                data['customer_code'] = data.get('id') or f"CUST-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['customer_code']
            if not data.get('created_date'):
                data['created_date'] = datetime.now().date().isoformat()
            if not data.get('customer_type'):
                data['customer_type'] = 'company'
            if not data.get('contact_person'):
                data['contact_person'] = data.get('company_name', 'Customer Representative')
            if not data.get('mobile'):
                data['mobile'] = ''
        return super().to_internal_value(data)

    def create(self, validated_data):
        customer = super().create(validated_data)
        incoming_contacts = getattr(self, '_incoming_contacts', None)
        if incoming_contacts and isinstance(incoming_contacts, list):
            for idx, c in enumerate(incoming_contacts):
                c_id = c.get('id') or f"CONT-{customer.id}-{idx + 1}"
                Contact.objects.update_or_create(
                    id=c_id,
                    defaults={
                        'customer_ref': customer,
                        'customer_id': customer.id,
                        'customer_name': customer.company_name,
                        'name': c.get('name') or customer.contact_person or 'Primary Contact',
                        'designation': c.get('designation') or customer.designation or '',
                        'department': c.get('department') or '',
                        'email': c.get('email') or customer.email or '',
                        'mobile': c.get('mobile') or c.get('phone') or customer.mobile or '',
                        'whatsapp': c.get('whatsapp') or customer.whatsapp or '',
                        'is_primary': c.get('isPrimary') or c.get('is_primary') or (idx == 0),
                    }
                )
        elif customer.contact_person:
            # Auto-create primary contact if none exists yet
            c_id = f"CONT-{customer.id}-1"
            Contact.objects.get_or_create(
                id=c_id,
                defaults={
                    'customer_ref': customer,
                    'customer_id': customer.id,
                    'customer_name': customer.company_name,
                    'name': customer.contact_person,
                    'designation': customer.designation or 'Primary Contact',
                    'department': 'Management',
                    'email': customer.email or '',
                    'mobile': customer.mobile or '',
                    'whatsapp': customer.whatsapp or '',
                    'is_primary': True,
                }
            )
        return customer

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['customerCode'] = instance.customer_code
        rep['customerType'] = instance.customer_type
        rep['companyName'] = instance.company_name
        rep['contactPerson'] = instance.contact_person
        rep['billingAddress'] = instance.billing_address
        rep['shippingAddress'] = instance.shipping_address
        rep['paymentTerms'] = instance.payment_terms
        rep['creditPeriodDays'] = instance.credit_period_days
        rep['creditLimit'] = float(instance.credit_limit or 0)
        rep['assignedSalesPerson'] = instance.assigned_sales_person
        rep['msmeNumber'] = instance.msme_number
        rep['taxCategory'] = instance.tax_category
        rep['bankName'] = instance.bank_name
        rep['bankAccountNo'] = instance.bank_account_no
        rep['bankAccountName'] = instance.bank_account_name
        rep['bankIfsc'] = instance.bank_ifsc
        rep['bankBranch'] = instance.bank_branch
        rep['linkedLeadId'] = instance.linked_lead_id
        rep['nearestPortRailway'] = instance.nearest_port_railway
        rep['inspectionRequirements'] = instance.inspection_requirements
        rep['specialInstructions'] = instance.special_instructions
        rep['status'] = instance.status
        rep['createdDate'] = str(instance.created_date) if instance.created_date else ''
        return rep


class EnquirySerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    machine_product = serializers.CharField(required=False, allow_blank=True, default='')
    requirement = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Enquiry
        fields = [
            'id',
            'enquiry_no',
            'lead_id',
            'customer_id',
            'customer_name',
            'customer_email',
            'contact_person',
            'contact_mobile',
            'enquiry_date',
            'requirement',
            'machine_product',
            'machine_type',
            'application',
            'capacity',
            'material_grade',
            'quantity',
            'unit_of_measure',
            'operating_conditions',
            'budget',
            'specification',
            'technical_clarifications',
            'attachments',
            'remarks',
            'expected_delivery',
            'assigned_person_id',
            'assigned_person_name',
            'status',
            'quotation_id',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'enquiryNo': 'enquiry_no',
            'enquiryNumber': 'enquiry_no',
            'leadId': 'lead_id',
            'lead': 'lead_id',
            'customerId': 'customer_id',
            'customer': 'customer_id',
            'customerName': 'customer_name',
            'companyName': 'customer_name',
            'customerEmail': 'customer_email',
            'email': 'customer_email',
            'contactPerson': 'contact_person',
            'contactMobile': 'contact_mobile',
            'mobile': 'contact_mobile',
            'phone': 'contact_mobile',
            'enquiryDate': 'enquiry_date',
            'machineProduct': 'machine_product',
            'machineType': 'machine_type',
            'materialGrade': 'material_grade',
            'unitOfMeasure': 'unit_of_measure',
            'operatingConditions': 'operating_conditions',
            'technicalClarifications': 'technical_clarifications',
            'expectedDelivery': 'expected_delivery',
            'assignedPersonId': 'assigned_person_id',
            'assignedPersonName': 'assigned_person_name',
            'quotationId': 'quotation_id',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if data.get('lead_id') and (not data.get('customer_name') or not data.get('contact_person') or not data.get('machine_product')):
            try:
                from .models import Lead
                ld = Lead.objects.filter(id=data['lead_id']).first() or Lead.objects.filter(lead_no=data['lead_id']).first()
                if ld:
                    if not data.get('customer_name') and ld.company_name:
                        data['customer_name'] = ld.company_name
                    if not data.get('contact_person') and ld.contact_person:
                        data['contact_person'] = ld.contact_person
                    if not data.get('contact_mobile') and ld.mobile:
                        data['contact_mobile'] = ld.mobile
                    if not data.get('customer_email') and ld.email:
                        data['customer_email'] = ld.email
                    if not data.get('machine_product') and ld.product_name:
                        data['machine_product'] = ld.product_name
            except Exception:
                pass
        if data.get('customer_id') and not data.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=data['customer_id']).first() or Customer.objects.filter(customer_code=data['customer_id']).first()
                if c:
                    data['customer_name'] = c.company_name
                    if not data.get('customer_email') and c.email:
                        data['customer_email'] = c.email
                    if not data.get('contact_person') and c.contact_person:
                        data['contact_person'] = c.contact_person
                    if not data.get('contact_mobile') and c.mobile:
                        data['contact_mobile'] = c.mobile
            except Exception:
                pass
        if not data.get('customer_name'):
            data['customer_name'] = data.get('company_name') or ''
        if not data.get('requirement'):
            data['requirement'] = data.get('description') or data.get('subject') or data.get('notes') or data.get('specification') or ''
        if not data.get('machine_product'):
            items = data.get('items', [])
            item_name = items[0].get('productName') or items[0].get('product_name') if items and isinstance(items, list) and isinstance(items[0], dict) else None
            data['machine_product'] = item_name or data.get('machineProduct') or data.get('productName') or data.get('subject') or ''
        if not data.get('enquiry_date'):
            data['enquiry_date'] = data.get('enquiryDate') or data.get('date') or datetime.now().date().isoformat()
        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('enquiry_no'):
                data['enquiry_no'] = data.get('enquiryNumber') or data.get('id') or f"ENQ-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['enquiry_no']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['enquiryNo'] = instance.enquiry_no
        rep['leadId'] = instance.lead_id or ''
        rep['customerId'] = instance.customer_id or ''

        cust_name = instance.customer_name or ''
        contact_p = instance.contact_person or ''
        contact_m = instance.contact_mobile or ''
        cust_email = instance.customer_email or ''
        prod_name = instance.machine_product or ''
        req = instance.requirement or ''
        spec = instance.specification or ''

        # Dynamic cross-resolution from linked Quotation, Lead, or Customer if missing or dummy
        if not cust_name or cust_name == 'Valued Customer' or not prod_name or prod_name == 'Process Equipment' or not contact_p or contact_p in ['Contact', 'Contact Person', 'N/A']:
            try:
                from .models import Quotation, Lead, Customer
                q_filter = models.Q(enquiry_id=instance.id) | models.Q(enquiry_id=instance.enquiry_no)
                if instance.quotation_id:
                    q_filter |= models.Q(id=instance.quotation_id) | models.Q(quotation_number=instance.quotation_id)
                q_filter |= models.Q(customer_id=f"cust-enq-{instance.id}") | models.Q(customer_id=f"cust-enq-{instance.enquiry_no}")
                q = Quotation.objects.filter(q_filter).exclude(customer_name='Valued Customer').first()
                if q:
                    if (not cust_name or cust_name == 'Valued Customer') and q.customer_name:
                        cust_name = q.customer_name
                    if not rep.get('leadId') and q.lead_id:
                        rep['leadId'] = q.lead_id
                    if (not contact_p or contact_p in ['Contact', 'Contact Person', 'N/A']) and q.contact_person:
                        contact_p = q.contact_person
                    if (not contact_m or contact_m == '9999999999') and q.contact_mobile:
                        contact_m = q.contact_mobile
                    if not cust_email and q.contact_email:
                        cust_email = q.contact_email
                    if (not prod_name or prod_name == 'Process Equipment') and q.machine_product and q.machine_product != 'Process Equipment':
                        prod_name = q.machine_product

                target_lead_id = rep.get('leadId') or instance.lead_id or (q.lead_id if q else None)
                if target_lead_id and ((not cust_name or cust_name == 'Valued Customer') or (not prod_name or prod_name == 'Process Equipment') or not contact_p or contact_p in ['Contact', 'Contact Person', 'N/A']):
                    ld = Lead.objects.filter(models.Q(id=target_lead_id) | models.Q(lead_no=target_lead_id)).exclude(company_name='Valued Customer').first()
                    if ld:
                        if (not cust_name or cust_name == 'Valued Customer') and ld.company_name:
                            cust_name = ld.company_name
                        if (not contact_p or contact_p in ['Contact', 'Contact Person', 'N/A']) and ld.contact_person:
                            contact_p = ld.contact_person
                        if (not contact_m or contact_m == '9999999999') and ld.mobile:
                            contact_m = ld.mobile
                        if not cust_email and ld.email:
                            cust_email = ld.email
                        if (not prod_name or prod_name == 'Process Equipment') and ld.product_name and ld.product_name != 'Process Equipment':
                            prod_name = ld.product_name

                if (not cust_name or cust_name == 'Valued Customer') and instance.customer_id:
                    c = Customer.objects.filter(models.Q(id=instance.customer_id) | models.Q(customer_code=instance.customer_id)).first()
                    if c:
                        if c.company_name: cust_name = c.company_name
                        if not contact_p and c.contact_person: contact_p = c.contact_person
                        if not contact_m and c.mobile: contact_m = c.mobile
                        if not cust_email and c.email: cust_email = c.email
            except Exception:
                pass

        if (req == 'Customer Requirement' or not req) and spec and spec != 'Customer Requirement':
            req = spec
        elif (not spec or spec == 'Customer Requirement') and req and req != 'Customer Requirement':
            spec = req

        rep['customerName'] = cust_name
        rep['customerEmail'] = cust_email
        rep['contactPerson'] = contact_p
        rep['contactMobile'] = contact_m
        rep['machineProduct'] = prod_name
        rep['requirement'] = req
        rep['specification'] = spec
        rep['quantity'] = instance.quantity if instance.quantity is not None else 1
        rep['enquiryDate'] = str(instance.enquiry_date) if instance.enquiry_date else ''
        rep['machineType'] = instance.machine_type or ''
        rep['application'] = instance.application or ''
        rep['capacity'] = instance.capacity or ''
        rep['materialGrade'] = instance.material_grade or ''
        rep['unitOfMeasure'] = instance.unit_of_measure or 'Unit'
        rep['operatingConditions'] = instance.operating_conditions or ''
        rep['budget'] = instance.budget or 0
        rep['technicalClarifications'] = instance.technical_clarifications or ''
        rep['attachments'] = instance.attachments or []
        rep['remarks'] = instance.remarks or ''
        rep['expectedDelivery'] = str(instance.expected_delivery) if instance.expected_delivery else ''
        rep['assignedPersonId'] = instance.assigned_person_id or ''
        rep['assignedPersonName'] = instance.assigned_person_name or 'Pravin Patel'
        rep['status'] = instance.status or 'new'
        rep['quotationId'] = instance.quotation_id or ''
        return rep


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'opportunity_no',
            'lead_id',
            'customer_id',
            'customer_name',
            'machine_product',
            'estimated_value',
            'expected_closing_date',
            'sales_person_id',
            'sales_person_name',
            'probability',
            'stage',
            'remarks',
            'quotation_id',
        ]


class FollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = [
            'id',
            'follow_up_no',
            'lead_or_customer_id',
            'lead_or_customer_name',
            'entity_type',
            'enquiry_id',
            'quotation_id',
            'type',
            'assigned_to_id',
            'assigned_to_name',
            'date',
            'time',
            'priority',
            'purpose',
            'notes',
            'next_follow_up_date',
            'status',
            'outcome',
            'customer_response',
            'completed_notes',
        ]


class SiteVisitSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    customer_id = serializers.CharField(required=False, allow_blank=True, default='')
    customer_name = serializers.CharField(required=False, allow_blank=True, default='')
    contact_person = serializers.CharField(required=False, allow_blank=True, default='')
    contact_mobile = serializers.CharField(required=False, allow_blank=True, default='')
    visit_date = serializers.CharField(required=False, allow_blank=True, default='')
    location = serializers.CharField(required=False, allow_blank=True, default='')
    purpose = serializers.CharField(required=False, allow_blank=True, default='')
    discussion_notes = serializers.CharField(required=False, allow_blank=True, default='')
    requirement_details = serializers.CharField(required=False, allow_blank=True, default='')
    outcome = serializers.CharField(required=False, allow_blank=True, default='positive')

    class Meta:
        model = SiteVisit
        fields = [
            'id',
            'visit_no',
            'customer_id',
            'customer_name',
            'lead_id',
            'enquiry_id',
            'contact_person',
            'contact_mobile',
            'visit_date',
            'location',
            'employee_id',
            'employee_name',
            'purpose',
            'discussion_notes',
            'requirement_details',
            'site_measurements',
            'operating_conditions',
            'technical_observations',
            'pending_clarifications',
            'attachments',
            'status',
            'outcome',
            'next_action',
            'next_follow_up_date',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'visitNo': 'visit_no',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'leadId': 'lead_id',
            'enquiryId': 'enquiry_id',
            'contactPerson': 'contact_person',
            'contactMobile': 'contact_mobile',
            'visitDate': 'visit_date',
            'employeeId': 'employee_id',
            'employeeName': 'employee_name',
            'discussionNotes': 'discussion_notes',
            'discussionSummary': 'discussion_notes',
            'requirementDetails': 'requirement_details',
            'siteMeasurements': 'site_measurements',
            'operatingConditions': 'operating_conditions',
            'technicalObservations': 'technical_observations',
            'pendingClarifications': 'pending_clarifications',
            'nextAction': 'next_action',
            'nextFollowUpDate': 'next_follow_up_date',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)

        if data.get('lead_id'):
            try:
                from .models import Lead
                lead = Lead.objects.filter(id=data['lead_id']).first()
                if lead:
                    if not data.get('customer_name'):
                        data['customer_name'] = lead.company_name
                    if not data.get('customer_id'):
                        data['customer_id'] = lead.id
                    if not data.get('contact_person'):
                        data['contact_person'] = lead.contact_person or 'Client Lead'
                    if not data.get('contact_mobile'):
                        data['contact_mobile'] = lead.mobile or ''
                    if not data.get('location'):
                        data['location'] = lead.address or lead.city or 'Client Site'
            except Exception:
                pass

        if not data.get('customer_name'):
            data['customer_name'] = 'Valued Client'
        if not data.get('customer_id'):
            data['customer_id'] = data.get('lead_id') or 'LEAD-PROSPECT'
        if not data.get('contact_person'):
            data['contact_person'] = 'Representative'
        if not data.get('contact_mobile'):
            data['contact_mobile'] = ''
        if not data.get('visit_date'):
            data['visit_date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('location'):
            data['location'] = 'Client Site'

        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('visit_no'):
                data['visit_no'] = data.get('id') or f"VST-2026-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['visit_no']

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['visitNo'] = ret.get('visit_no')
        ret['customerId'] = ret.get('customer_id')
        ret['customerName'] = ret.get('customer_name')
        ret['leadId'] = ret.get('lead_id')
        ret['enquiryId'] = ret.get('enquiry_id')
        ret['contactPerson'] = ret.get('contact_person')
        ret['contactMobile'] = ret.get('contact_mobile')
        ret['visitDate'] = ret.get('visit_date')
        ret['employeeId'] = ret.get('employee_id')
        ret['employeeName'] = ret.get('employee_name')
        ret['discussionNotes'] = ret.get('discussion_notes')
        ret['requirementDetails'] = ret.get('requirement_details')
        ret['siteMeasurements'] = ret.get('site_measurements')
        ret['operatingConditions'] = ret.get('operating_conditions')
        ret['technicalObservations'] = ret.get('technical_observations')
        ret['pendingClarifications'] = ret.get('pending_clarifications')
        ret['nextAction'] = ret.get('next_action')
        ret['nextFollowUpDate'] = ret.get('next_follow_up_date')
        return ret


class ExhibitionSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Exhibition
        fields = [
            'id',
            'expo_name',
            'organizer',
            'location',
            'venue',
            'city',
            'country',
            'participation_status',
            'start_date',
            'end_date',
            'stall_number',
            'contact_person',
            'budget',
            'actual_expenses',
            'assigned_team',
            'products_displayed',
            'notes',
            'total_contacts',
            'qualified_leads',
            'quotations_sent',
            'converted_customers',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'expoName': 'expo_name',
            'startDate': 'start_date',
            'endDate': 'end_date',
            'stallNumber': 'stall_number',
            'contactPerson': 'contact_person',
            'participationStatus': 'participation_status',
            'actualExpenses': 'actual_expenses',
            'assignedTeam': 'assigned_team',
            'productsDisplayed': 'products_displayed',
            'totalContacts': 'total_contacts',
            'qualifiedLeads': 'qualified_leads',
            'quotationsSent': 'quotations_sent',
            'convertedCustomers': 'converted_customers',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)

        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('id'):
                data['id'] = f"EXPO-2026-{int(datetime.now().timestamp())}"
            if not data.get('expo_name'):
                data['expo_name'] = 'Industry Expo'
            if not data.get('location'):
                data['location'] = 'Exhibition Center'
            if not data.get('start_date'):
                data['start_date'] = datetime.now().strftime('%Y-%m-%d')
            if not data.get('end_date'):
                data['end_date'] = datetime.now().strftime('%Y-%m-%d')

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['expoName'] = ret.get('expo_name')
        ret['startDate'] = ret.get('start_date')
        ret['endDate'] = ret.get('end_date')
        ret['stallNumber'] = ret.get('stall_number')
        ret['contactPerson'] = ret.get('contact_person')
        ret['participationStatus'] = ret.get('participation_status')
        ret['actualExpenses'] = ret.get('actual_expenses')
        ret['assignedTeam'] = ret.get('assigned_team')
        ret['productsDisplayed'] = ret.get('products_displayed')
        ret['totalContacts'] = ret.get('total_contacts')
        ret['qualifiedLeads'] = ret.get('qualified_leads')
        ret['quotationsSent'] = ret.get('quotations_sent')
        ret['convertedCustomers'] = ret.get('converted_customers')
        return ret


class QuotationSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    quotationNumber = serializers.CharField(source='quotation_number', required=False)
    currentRevision = serializers.CharField(source='current_revision', required=False)
    validUntil = serializers.CharField(source='valid_until', required=False, allow_blank=True)
    customerId = serializers.CharField(source='customer_id', required=False)
    customerName = serializers.CharField(source='customer_name', required=False)
    contactPerson = serializers.CharField(source='contact_person', required=False, allow_blank=True)
    contactMobile = serializers.CharField(source='contact_mobile', required=False, allow_blank=True)
    contactEmail = serializers.CharField(source='contact_email', required=False, allow_blank=True)
    enquiryId = serializers.CharField(source='enquiry_id', required=False, allow_blank=True, allow_null=True)
    opportunityId = serializers.CharField(source='opportunity_id', required=False, allow_blank=True, allow_null=True)
    salesPersonId = serializers.CharField(source='sales_person_id', required=False, allow_blank=True)
    salesPersonName = serializers.CharField(source='sales_person_name', required=False, allow_blank=True)

    class Meta:
        model = Quotation
        fields = '__all__'

    def to_internal_value(self, data):
        inst = getattr(self, 'instance', None)
        ret = {}
        ret['id'] = data.get('id') or data.get('quotationNumber') or data.get('quotation_number') or (inst.id if inst else None)
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or ret.get('id') or (inst.quotation_number if inst else '')
        ret['current_revision'] = data.get('current_revision') or data.get('currentRevision') or (inst.current_revision if inst else 'Rev-00')
        ret['date'] = data.get('date') or (inst.date if inst else datetime.now().strftime('%Y-%m-%d'))
        ret['valid_until'] = data.get('valid_until') or data.get('validUntil') or (inst.valid_until if inst else '')
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or data.get('customer') or (inst.customer_id if inst else '')
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or (inst.customer_name if inst else '')
        if ret.get('customer_id') and not ret.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=ret['customer_id']).first() or Customer.objects.filter(customer_code=ret['customer_id']).first()
                if c:
                    ret['customer_name'] = c.company_name
            except Exception:
                pass
        if not ret.get('customer_name'):
            ret['customer_name'] = data.get('company_name') or data.get('companyName') or 'Valued Customer'
        ret['contact_person'] = data.get('contact_person') or data.get('contactPerson') or (inst.contact_person if inst else '')
        ret['contact_mobile'] = data.get('contact_mobile') or data.get('contactMobile') or (inst.contact_mobile if inst else '')
        ret['contact_email'] = data.get('contact_email') or data.get('contactEmail') or data.get('email') or (inst.contact_email if inst else '')
        ret['enquiry_id'] = data.get('enquiry_id') or data.get('enquiryId') or data.get('enquiry') or (inst.enquiry_id if inst else None)
        ret['opportunity_id'] = data.get('opportunity_id') or data.get('opportunityId') or (inst.opportunity_id if inst else None)
        ret['sales_person_id'] = data.get('sales_person_id') or data.get('salesPersonId') or (inst.sales_person_id if inst else '')
        ret['sales_person_name'] = data.get('sales_person_name') or data.get('salesPersonName') or (inst.sales_person_name if inst else '')
        ret['status'] = data.get('status') or (inst.status if inst else 'draft')
        ret['lead_id'] = data.get('lead_id') or data.get('leadId') or (inst.lead_id if inst else None)
        ret['machine_product'] = str(data.get('machine_product') or data.get('machineProduct') or (inst.machine_product if inst else '') or '')

        # Auto-heal contact_email, contact_person, contact_mobile from Lead / Enquiry / Customer if missing
        if not ret.get('contact_email') or not ret.get('contact_mobile') or not ret.get('contact_person'):
            try:
                from .models import Lead, Enquiry, Customer
                from django.db.models import Q

                # 1. Check direct lead_id
                if ret.get('lead_id'):
                    ld = Lead.objects.filter(Q(id=ret['lead_id']) | Q(lead_no=ret['lead_id'])).first()
                    if ld:
                        if not ret.get('contact_email') and ld.email:
                            ret['contact_email'] = ld.email
                        if not ret.get('contact_person') and ld.contact_person:
                            ret['contact_person'] = ld.contact_person
                        if not ret.get('contact_mobile') and ld.mobile:
                            ret['contact_mobile'] = ld.mobile

                # 2. Check enquiry_id
                if (not ret.get('contact_email') or not ret.get('lead_id')) and ret.get('enquiry_id'):
                    enq = Enquiry.objects.filter(Q(id=ret['enquiry_id']) | Q(enquiry_no=ret['enquiry_id'])).first()
                    if enq:
                        if not ret.get('contact_email') and enq.customer_email:
                            ret['contact_email'] = enq.customer_email
                        if not ret.get('lead_id') and enq.lead_id:
                            ret['lead_id'] = enq.lead_id
                            ld_enq = Lead.objects.filter(Q(id=enq.lead_id) | Q(lead_no=enq.lead_id)).first()
                            if ld_enq:
                                if not ret.get('contact_email') and ld_enq.email:
                                    ret['contact_email'] = ld_enq.email
                                if not ret.get('contact_person') and ld_enq.contact_person:
                                    ret['contact_person'] = ld_enq.contact_person
                                if not ret.get('contact_mobile') and ld_enq.mobile:
                                    ret['contact_mobile'] = ld_enq.mobile
                        if not ret.get('contact_person') and enq.contact_person:
                            ret['contact_person'] = enq.contact_person
                        if not ret.get('contact_mobile') and enq.contact_mobile:
                            ret['contact_mobile'] = enq.contact_mobile

                # 3. Check customer_id
                if not ret.get('contact_email') and ret.get('customer_id'):
                    c_obj = Customer.objects.filter(Q(id=ret['customer_id']) | Q(customer_code=ret['customer_id'])).first()
                    if c_obj:
                        if not ret.get('contact_email') and c_obj.email:
                            ret['contact_email'] = c_obj.email
                        if not ret.get('contact_person') and c_obj.contact_person:
                            ret['contact_person'] = c_obj.contact_person
                        if not ret.get('contact_mobile') and c_obj.mobile:
                            ret['contact_mobile'] = c_obj.mobile

                # 4. Fallback search by company name in Lead database
                if not ret.get('contact_email') and ret.get('customer_name'):
                    ld_name = Lead.objects.filter(company_name__iexact=str(ret['customer_name']).strip()).exclude(email='').first()
                    if ld_name and ld_name.email:
                        ret['contact_email'] = ld_name.email
                        if not ret.get('lead_id'):
                            ret['lead_id'] = ld_name.id
                        if not ret.get('contact_person') and ld_name.contact_person:
                            ret['contact_person'] = ld_name.contact_person
                        if not ret.get('contact_mobile') and ld_name.mobile:
                            ret['contact_mobile'] = ld_name.mobile
            except Exception:
                pass

        raw_summary = data.get('latest_summary') if 'latest_summary' in data else data.get('latestSummary')
        if raw_summary is None and inst:
            raw_summary = inst.latest_summary
        if isinstance(raw_summary, (dict, list)):
            import json
            ret['latest_summary'] = json.dumps(raw_summary)
        else:
            ret['latest_summary'] = str(raw_summary or '')

        ret['subtotal'] = float(data.get('subtotal') or (inst.subtotal if inst else 0))
        ret['tax_amount'] = float(data.get('tax_amount') or data.get('taxAmount') or (inst.tax_amount if inst else 0))
        ret['total_amount'] = float(data.get('total_amount') or data.get('totalAmount') or data.get('grand_total') or data.get('grandTotal') or (inst.total_amount if inst else 0))
        ret['grand_total'] = float(data.get('grand_total') or data.get('grandTotal') or ret['total_amount'] or (inst.grand_total if inst else 0))
        ret['items'] = data.get('items') or (inst.items if inst else [])
        ret['approved_by'] = str(data.get('approved_by') or data.get('approvedBy') or (inst.approved_by if inst else '') or '')
        ret['rejection_reason'] = str(data.get('rejection_reason') or data.get('rejectionReason') or (inst.rejection_reason if inst else '') or '')

        if 'revisions' in data:
            ret['revisions'] = data.get('revisions') or []
        elif inst and inst.revisions:
            ret['revisions'] = inst.revisions
        else:
            ret['revisions'] = [{
                'revisionNumber': 'Rev-00',
                'revisionDate': ret.get('date'),
                'items': ret.get('items'),
                'subtotal': ret.get('subtotal'),
                'taxAmount': ret.get('tax_amount'),
                'grandTotal': ret.get('total_amount'),
                'status': ret.get('status'),
            }]

        # Ensure top-level items and financial totals are populated from active revision
        revs = ret.get('revisions') or []
        cur_rev = ret.get('current_revision') or 'Rev-00'
        active_rev = None
        for r in revs:
            if isinstance(r, dict) and r.get('revisionNumber') == cur_rev:
                active_rev = r
                break
        if not active_rev and revs and isinstance(revs[-1], dict):
            active_rev = revs[-1]

        if active_rev:
            if not ret.get('items'):
                ret['items'] = active_rev.get('items') or []
            if not ret.get('subtotal'):
                ret['subtotal'] = float(active_rev.get('subTotal') or active_rev.get('subtotal') or 0)
            if not ret.get('tax_amount'):
                ret['tax_amount'] = float(active_rev.get('taxAmount') or active_rev.get('tax_amount') or 0)
            if not ret.get('grand_total'):
                ret['grand_total'] = float(active_rev.get('grandTotal') or active_rev.get('grand_total') or 0)
            if not ret.get('total_amount'):
                ret['total_amount'] = ret['grand_total']
            if not ret.get('machine_product') and ret.get('items'):
                first_it = ret['items'][0]
                ret['machine_product'] = first_it.get('productName') or first_it.get('product_name') or ''

        ret['notes'] = str((data.get('notes') if 'notes' in data else (inst.notes if inst else '')) or '')

        # Remove primary key 'id' if updating an existing record to avoid DB PK conflict
        if inst:
            ret.pop('id', None)

        return ret

    def update(self, instance, validated_data):
        for k in ['rejection_reason', 'notes', 'machine_product', 'approved_by', 'contact_person', 'contact_mobile', 'contact_email', 'sales_person_id', 'sales_person_name']:
            if getattr(instance, k, None) is None:
                setattr(instance, k, '')
        for attr, value in validated_data.items():
            if value is None and attr in ['rejection_reason', 'notes', 'machine_product', 'approved_by', 'contact_person', 'contact_mobile', 'contact_email', 'sales_person_id', 'sales_person_name']:
                value = ''
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['quotationNumber'] = instance.quotation_number
        rep['currentRevision'] = instance.current_revision
        rep['date'] = instance.date
        rep['validUntil'] = instance.valid_until
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['contactPerson'] = instance.contact_person
        rep['contactMobile'] = instance.contact_mobile
        rep['contactEmail'] = instance.contact_email
        rep['leadId'] = instance.lead_id
        rep['enquiryId'] = instance.enquiry_id
        rep['opportunityId'] = instance.opportunity_id
        import json
        revs = instance.revisions or []
        if isinstance(revs, str):
            try:
                revs = json.loads(revs)
            except Exception:
                revs = []

        cur_rev = instance.current_revision or 'Rev-00'
        active_rev = None
        for r in revs:
            if isinstance(r, dict) and str(r.get('revisionNumber') or '').strip().lower() == str(cur_rev).strip().lower():
                active_rev = r
                break
        if not active_rev and revs and isinstance(revs[-1], dict):
            active_rev = revs[-1]

        inst_items = instance.items or []
        if isinstance(inst_items, str):
            try:
                inst_items = json.loads(inst_items)
            except Exception:
                inst_items = []

        items = (active_rev.get('items') if active_rev and active_rev.get('items') else None) or inst_items or []

        if active_rev and (active_rev.get('subTotal') is not None or active_rev.get('subtotal') is not None):
            subtotal = float(active_rev.get('subTotal') if active_rev.get('subTotal') is not None else active_rev.get('subtotal'))
        else:
            subtotal = float(instance.subtotal or 0)

        if active_rev and (active_rev.get('taxAmount') is not None or active_rev.get('tax_amount') is not None):
            tax_amount = float(active_rev.get('taxAmount') if active_rev.get('taxAmount') is not None else active_rev.get('tax_amount'))
        else:
            tax_amount = float(instance.tax_amount or 0)

        if active_rev and (active_rev.get('grandTotal') is not None or active_rev.get('grand_total') is not None):
            grand_total = float(active_rev.get('grandTotal') if active_rev.get('grandTotal') is not None else active_rev.get('grand_total'))
        else:
            grand_total = float(instance.grand_total or instance.total_amount or 0)

        first_item = (items or [{}])[0]
        machine_prod = instance.machine_product or first_item.get('productName') or first_item.get('product_name') or 'Process Equipment'

        rep['machineProduct'] = machine_prod
        rep['salesPersonId'] = instance.sales_person_id
        rep['salesPersonName'] = instance.sales_person_name
        rep['revisions'] = revs
        rep['items'] = items
        rep['subtotal'] = subtotal
        rep['taxAmount'] = tax_amount
        rep['totalAmount'] = grand_total
        rep['grandTotal'] = grand_total
        rep['status'] = instance.status
        rep['approvedBy'] = instance.approved_by
        rep['approvedAt'] = instance.approved_at.isoformat() if instance.approved_at else None
        rep['rejectionReason'] = instance.rejection_reason
        rep['notes'] = instance.notes
        
        # Calculate latestSummary for frontend convenience
        rep['latestSummary'] = {
            'machineProduct': machine_prod,
            'grandTotal': grand_total,
            'status': instance.status or (active_rev.get('status') if active_rev else 'draft')
        }
        return rep


class CustomerPOSerializer(serializers.ModelSerializer):
    poNumber = serializers.CharField(source='po_number', required=False)
    internalCpoNo = serializers.CharField(source='internal_cpo_no', required=False, allow_blank=True)
    customerId = serializers.CharField(source='customer_id', required=False)
    customerName = serializers.CharField(source='customer_name', required=False)
    quotationId = serializers.CharField(source='quotation_id', required=False, allow_blank=True, allow_null=True)
    quotationNumber = serializers.CharField(source='quotation_number', required=False, allow_blank=True)
    poDate = serializers.CharField(source='po_date', required=False)
    receivedDate = serializers.CharField(source='received_date', required=False, allow_blank=True)
    deliveryDate = serializers.CharField(source='delivery_date', required=False, allow_blank=True)
    poAmount = serializers.FloatField(source='po_value', required=False)
    poValue = serializers.FloatField(source='po_value', required=False)
    scopeOfWork = serializers.CharField(source='scope_of_work', required=False, allow_blank=True)
    paymentTerms = serializers.CharField(source='payment_terms', required=False, allow_blank=True)
    poDocumentUrl = serializers.CharField(source='po_document_url', required=False, allow_blank=True)
    attachmentUrl = serializers.CharField(source='attachment_url', required=False, allow_blank=True)
    convertedSoId = serializers.CharField(source='converted_so_id', required=False, allow_blank=True, allow_null=True)
    salesOrderId = serializers.CharField(source='converted_so_id', required=False, allow_blank=True, allow_null=True)
    specialConditions = serializers.CharField(source='special_conditions', required=False, allow_blank=True)

    class Meta:
        model = CustomerPO
        fields = '__all__'

    def to_internal_value(self, data):
        inst = getattr(self, 'instance', None)
        ret = {}
        if inst:
            ret['id'] = inst.id
            ret['po_number'] = inst.po_number
        else:
            ret['id'] = data.get('id') or data.get('internal_cpo_no') or data.get('internalCpoNo') or data.get('po_number') or data.get('poNumber') or None
            ret['po_number'] = data.get('po_number') or data.get('poNumber') or ret.get('id') or 'PO/GEN'
        ret['internal_cpo_no'] = data.get('internal_cpo_no') or data.get('internalCpoNo') or (inst.internal_cpo_no if inst else '')
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or data.get('customer') or (inst.customer_id if inst else '')
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or (inst.customer_name if inst else '')
        if ret.get('customer_id') and not ret.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=ret['customer_id']).first() or Customer.objects.filter(customer_code=ret['customer_id']).first()
                if c:
                    ret['customer_name'] = c.company_name
            except Exception:
                pass
        if not ret.get('customer_name'):
            ret['customer_name'] = data.get('company_name') or data.get('companyName') or 'Valued Customer'
        ret['quotation_id'] = data.get('quotation_id') or data.get('quotationId') or data.get('quotation') or (inst.quotation_id if inst else None)
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or (inst.quotation_number if inst else '')
        ret['po_date'] = data.get('po_date') or data.get('poDate') or (inst.po_date if inst else datetime.now().strftime('%Y-%m-%d'))
        ret['received_date'] = data.get('received_date') or data.get('receivedDate') or (inst.received_date if inst else ret['po_date'])
        ret['delivery_date'] = data.get('delivery_date') or data.get('deliveryDate') or (inst.delivery_date if inst else '')
        
        po_val = data.get('po_value') if 'po_value' in data else (data.get('poValue') if 'poValue' in data else (data.get('orderValue') if 'orderValue' in data else (data.get('order_value') if 'order_value' in data else (data.get('poAmount') if 'poAmount' in data else (data.get('po_amount') if 'po_amount' in data else None)))))
        if po_val is not None:
            ret['po_value'] = float(po_val)
        elif inst:
            ret['po_value'] = inst.po_value
        else:
            ret['po_value'] = 0.0

        ret['po_amount'] = ret['po_value']
        ret['scope_of_work'] = data.get('scope_of_work') or data.get('scopeOfWork') or data.get('remarks') or (inst.scope_of_work if inst else '')
        ret['remarks'] = data.get('remarks') or ret['scope_of_work']
        ret['payment_terms'] = data.get('payment_terms') or data.get('paymentTerms') or (inst.payment_terms if inst else '')
        ret['po_document_url'] = data.get('po_document_url') or data.get('poDocumentUrl') or (inst.po_document_url if inst else '')
        ret['attachment_url'] = data.get('attachment_url') or data.get('attachmentUrl') or ret['po_document_url']
        ret['status'] = data.get('status') or (inst.status if inst else 'received')
        ret['converted_so_id'] = data.get('converted_so_id') or data.get('convertedSoId') or data.get('salesOrderId') or data.get('sales_order_id') or (inst.converted_so_id if inst else None)
        ret['sales_order_id'] = ret['converted_so_id']
        ret['special_conditions'] = data.get('special_conditions') or data.get('specialConditions') or (inst.special_conditions if inst else '')
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['poNumber'] = instance.po_number
        rep['internalCpoNo'] = instance.internal_cpo_no
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['quotationId'] = instance.quotation_id
        rep['quotationNumber'] = instance.quotation_number
        rep['poDate'] = instance.po_date
        rep['receivedDate'] = instance.received_date
        rep['deliveryDate'] = instance.delivery_date
        rep['poAmount'] = instance.po_amount or instance.po_value
        rep['poValue'] = instance.po_value
        rep['scopeOfWork'] = instance.scope_of_work
        rep['remarks'] = instance.remarks or instance.scope_of_work
        rep['paymentTerms'] = instance.payment_terms
        rep['poDocumentUrl'] = instance.po_document_url
        rep['attachmentUrl'] = instance.attachment_url or instance.po_document_url
        rep['status'] = instance.status
        rep['convertedSoId'] = instance.converted_so_id
        rep['salesOrderId'] = instance.sales_order_id or instance.converted_so_id
        rep['specialConditions'] = instance.special_conditions
        return rep


class SalesOrderSerializer(serializers.ModelSerializer):
    salesOrderNumber = serializers.CharField(source='sales_order_number', required=False)
    customerPoId = serializers.CharField(source='customer_po_id', required=False, allow_blank=True, allow_null=True)
    customerPoNumber = serializers.CharField(source='customer_po_number', required=False, allow_blank=True)
    quotationId = serializers.CharField(source='quotation_id', required=False, allow_blank=True, allow_null=True)
    quotationNumber = serializers.CharField(source='quotation_number', required=False, allow_blank=True)
    customerId = serializers.CharField(source='customer_id', required=False)
    customerName = serializers.CharField(source='customer_name', required=False)
    orderDate = serializers.CharField(source='order_date', required=False)
    targetDeliveryDate = serializers.CharField(source='target_delivery_date', required=False, allow_blank=True)
    deliveryDate = serializers.CharField(source='delivery_date', required=False, allow_blank=True)
    totalAmount = serializers.FloatField(source='total_amount', required=False)
    taxAmount = serializers.FloatField(source='tax_amount', required=False)
    grandTotal = serializers.FloatField(source='grand_total', required=False)
    orderValue = serializers.FloatField(source='order_value', required=False)
    paymentTerms = serializers.CharField(source='payment_terms', required=False, allow_blank=True)
    billingAddress = serializers.CharField(source='billing_address', required=False, allow_blank=True)
    shippingAddress = serializers.CharField(source='shipping_address', required=False, allow_blank=True)
    projectId = serializers.CharField(source='project_id', required=False, allow_blank=True, allow_null=True)
    jobNumber = serializers.CharField(source='job_number', required=False, allow_blank=True)
    assignedProjectManager = serializers.CharField(source='assigned_project_manager', required=False, allow_blank=True)
    createdBy = serializers.CharField(source='created_by', required=False, allow_blank=True)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)

    class Meta:
        model = SalesOrder
        fields = '__all__'

    def to_internal_value(self, data):
        inst = getattr(self, 'instance', None)
        ret = {}
        if inst:
            ret['id'] = inst.id
            ret['sales_order_number'] = inst.sales_order_number
        else:
            ret['id'] = data.get('id') or data.get('salesOrderNumber') or data.get('sales_order_number') or None
            ret['sales_order_number'] = data.get('sales_order_number') or data.get('salesOrderNumber') or ret.get('id') or 'SO-GEN'
        ret['customer_po_id'] = data.get('customer_po_id') or data.get('customerPoId') or data.get('customerPo') or data.get('customer_po') or (inst.customer_po_id if inst else None)
        ret['customer_po_number'] = data.get('customer_po_number') or data.get('customerPoNumber') or (inst.customer_po_number if inst else '')
        ret['quotation_id'] = data.get('quotation_id') or data.get('quotationId') or data.get('quotation') or (inst.quotation_id if inst else None)
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or (inst.quotation_number if inst else '')
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or data.get('customer') or (inst.customer_id if inst else '')
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or (inst.customer_name if inst else '')
        if ret.get('customer_id') and not ret.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=ret['customer_id']).first() or Customer.objects.filter(customer_code=ret['customer_id']).first()
                if c:
                    ret['customer_name'] = c.company_name
            except Exception:
                pass
        if not ret.get('customer_name'):
            ret['customer_name'] = data.get('company_name') or data.get('companyName') or 'Valued Customer'
        ret['order_date'] = data.get('order_date') or data.get('orderDate') or (inst.order_date if inst else datetime.now().strftime('%Y-%m-%d'))
        ret['target_delivery_date'] = data.get('target_delivery_date') or data.get('targetDeliveryDate') or data.get('deliveryDate') or data.get('delivery_date') or (inst.target_delivery_date if inst else '')
        ret['delivery_date'] = data.get('delivery_date') or data.get('deliveryDate') or ret['target_delivery_date']
        
        if 'items' in data:
            ret['items'] = data.get('items') or []
        elif inst:
            ret['items'] = inst.items or []
        else:
            ret['items'] = []
            
        tot_val = data.get('total_amount') if 'total_amount' in data else (data.get('totalAmount') if 'totalAmount' in data else (data.get('subtotal') if 'subtotal' in data else (data.get('orderValue') if 'orderValue' in data else None)))
        if tot_val is not None:
            ret['total_amount'] = float(tot_val)
        elif inst:
            ret['total_amount'] = inst.total_amount
        else:
            ret['total_amount'] = 0.0

        tax_val = data.get('tax_amount') if 'tax_amount' in data else (data.get('taxAmount') if 'taxAmount' in data else None)
        if tax_val is not None:
            ret['tax_amount'] = float(tax_val)
        elif inst:
            ret['tax_amount'] = inst.tax_amount
        else:
            ret['tax_amount'] = 0.0

        gt_val = data.get('grand_total') if 'grand_total' in data else (data.get('grandTotal') if 'grandTotal' in data else (data.get('orderValue') if 'orderValue' in data else (data.get('order_value') if 'order_value' in data else None)))
        if gt_val is not None:
            ret['grand_total'] = float(gt_val)
        elif inst:
            ret['grand_total'] = inst.grand_total
        else:
            ret['grand_total'] = ret['total_amount']

        ret['order_value'] = float(data.get('order_value') or data.get('orderValue') or ret['grand_total'] or 0)
        ret['payment_terms'] = data.get('payment_terms') or data.get('paymentTerms') or (inst.payment_terms if inst else '')
        ret['billing_address'] = data.get('billing_address') or data.get('billingAddress') or (inst.billing_address if inst else '')
        ret['shipping_address'] = data.get('shipping_address') or data.get('shippingAddress') or (inst.shipping_address if inst else '')
        ret['status'] = data.get('status') or (inst.status if inst else 'confirmed')
        ret['project_id'] = data.get('project_id') or data.get('projectId') or (inst.project_id if inst else None)
        ret['job_number'] = data.get('job_number') or data.get('jobNumber') or (inst.job_number if inst else '')
        ret['assigned_project_manager'] = data.get('assigned_project_manager') or data.get('assignedProjectManager') or data.get('project_manager_name') or ''
        ret['created_by'] = data.get('created_by') or data.get('createdBy') or (inst.created_by if inst else '')
        ret['approved_by'] = data.get('approved_by') or data.get('approvedBy') or (inst.approved_by if inst else '')
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['salesOrderNumber'] = instance.sales_order_number
        rep['customerPoId'] = instance.customer_po_id
        rep['customerPoNumber'] = instance.customer_po_number
        rep['quotationId'] = instance.quotation_id
        rep['quotationNumber'] = instance.quotation_number
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['orderDate'] = instance.order_date
        rep['targetDeliveryDate'] = instance.target_delivery_date
        rep['deliveryDate'] = instance.delivery_date or instance.target_delivery_date
        rep['items'] = instance.items or []
        rep['totalAmount'] = instance.total_amount
        rep['taxAmount'] = instance.tax_amount
        rep['grandTotal'] = instance.grand_total
        rep['orderValue'] = instance.order_value or instance.grand_total
        rep['paymentTerms'] = instance.payment_terms
        rep['billingAddress'] = instance.billing_address
        rep['shippingAddress'] = instance.shipping_address
        rep['status'] = instance.status
        rep['projectId'] = instance.project_id
        rep['jobNumber'] = instance.job_number
        rep['assignedProjectManager'] = instance.assigned_project_manager
        rep['createdBy'] = instance.created_by
        rep['approvedBy'] = instance.approved_by
        return rep


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'title',
            'description',
            'performed_by',
            'performed_at',
            'type',
        ]
