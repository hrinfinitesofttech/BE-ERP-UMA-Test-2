from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.core.models import NumberingSetting, AuditLog
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
from .serializers import (
    LeadSerializer,
    CustomerSerializer,
    ContactSerializer,
    EnquirySerializer,
    OpportunitySerializer,
    FollowUpSerializer,
    SiteVisitSerializer,
    ExhibitionSerializer,
    QuotationSerializer,
    CustomerPOSerializer,
    SalesOrderSerializer,
    ActivitySerializer,
)


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all().order_by('-id')
    serializer_class = LeadSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('lead_no') or not data.get('leadNo'):
            # Auto-assign lead number from numbering engine
            num_setting = NumberingSetting.objects.filter(doc_type='lead').first()
            if num_setting:
                code = num_setting.generate_next_number(increment=True)
            else:
                code = f"LEAD-2026-{Lead.objects.count() + 101:04d}"
            data['id'] = code
            data['lead_no'] = code
        if not data.get('created_date') and not data.get('createdDate'):
            data['created_date'] = datetime.now().strftime('%Y-%m-%d')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert')
    def convert_to_customer(self, request, pk=None):
        lead = self.get_object()

        # 1. Create or retrieve Customer
        cust_code = f"CUST-{Customer.objects.count() + 1:03d}"
        cust_id = f"CUST-2026-{Customer.objects.count() + 1:04d}"

        customer = Customer.objects.create(
            id=cust_id,
            customer_code=cust_code,
            customer_type='company',
            company_name=lead.company_name,
            industry=lead.industry,
            gstin=lead.gstin,
            website=lead.website,
            contact_person=lead.contact_person,
            designation=lead.designation,
            mobile=lead.mobile,
            email=lead.email,
            whatsapp=lead.whatsapp,
            billing_address=lead.address,
            shipping_address=lead.address,
            city=lead.city,
            state=lead.state,
            country=lead.country,
            pincode=lead.pincode,
            assigned_sales_person=lead.assigned_sales_person_name,
            created_date=datetime.now().strftime('%Y-%m-%d'),
        )

        # 2. Also create Enquiry
        enq_num = NumberingSetting.objects.filter(doc_type='enquiry').first()
        enq_code = enq_num.generate_next_number(increment=True) if enq_num else f"ENQ-2026-{Enquiry.objects.count() + 1:04d}"

        enquiry = Enquiry.objects.create(
            id=enq_code,
            enquiry_no=enq_code,
            lead_id=lead.id,
            customer_id=customer.id,
            customer_name=customer.company_name,
            enquiry_date=datetime.now().strftime('%Y-%m-%d'),
            requirement=lead.requirement_description or f"Machine enquiry for {lead.product_name}",
            machine_product=lead.product_name,
            quantity=lead.quantity,
            specification=f"Capacity: {lead.capacity}, Application: {lead.application}",
            expected_delivery=lead.expected_delivery,
            assigned_person_id=lead.assigned_sales_person_id,
            assigned_person_name=lead.assigned_sales_person_name,
            status='new',
        )

        # 3. Also create Opportunity
        opp_num = NumberingSetting.objects.filter(doc_type='opportunity').first()
        opp_code = opp_num.generate_next_number(increment=True) if opp_num else f"OPP-2026-{Opportunity.objects.count() + 1:04d}"

        opportunity = Opportunity.objects.create(
            id=opp_code,
            opportunity_no=opp_code,
            lead_id=lead.id,
            customer_id=customer.id,
            customer_name=customer.company_name,
            machine_product=lead.product_name,
            estimated_value=lead.budget,
            expected_closing_date=lead.expected_delivery,
            sales_person_id=lead.assigned_sales_person_id,
            sales_person_name=lead.assigned_sales_person_name,
            probability=60,
            stage='qualification',
        )

        # Update Lead status
        lead.status = 'won'
        lead.converted_customer_id = customer.id
        lead.converted_enquiry_id = enquiry.id
        lead.converted_opportunity_id = opportunity.id
        lead.save(update_fields=['status', 'converted_customer_id', 'converted_enquiry_id', 'converted_opportunity_id'])

        return Response({
            'success': True,
            'customer': CustomerSerializer(customer).data,
            'enquiry': EnquirySerializer(enquiry).data,
            'opportunity': OpportunitySerializer(opportunity).data,
        })


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id'):
            data['id'] = f"CUST-2026-{Customer.objects.count() + 1:04d}"
        if not data.get('customer_code') and not data.get('customerCode'):
            data['customer_code'] = f"CUST-{Customer.objects.count() + 1:03d}"
        if not data.get('created_date') and not data.get('createdDate'):
            data['created_date'] = datetime.now().strftime('%Y-%m-%d')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all().order_by('name')
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]


class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.all().order_by('-id')
    serializer_class = EnquirySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('enquiry_no') and not data.get('enquiryNo'):
            num_setting = NumberingSetting.objects.filter(doc_type='enquiry').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"ENQ-2026-{Enquiry.objects.count() + 1:04d}"
            data['id'] = code
            data['enquiry_no'] = code
        if not data.get('enquiry_date') and not data.get('enquiryDate'):
            data['enquiry_date'] = datetime.now().strftime('%Y-%m-%d')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all().order_by('-id')
    serializer_class = OpportunitySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('opportunity_no') and not data.get('opportunityNo'):
            num_setting = NumberingSetting.objects.filter(doc_type='opportunity').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"OPP-2026-{Opportunity.objects.count() + 1:04d}"
            data['id'] = code
            data['opportunity_no'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FollowUpViewSet(viewsets.ModelViewSet):
    queryset = FollowUp.objects.all().order_by('-date')
    serializer_class = FollowUpSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('follow_up_no') and not data.get('followUpNo'):
            code = f"FLW-2026-{FollowUp.objects.count() + 1:04d}"
            data['id'] = code
            data['follow_up_no'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_follow_up(self, request, pk=None):
        flw = self.get_object()
        flw.status = 'completed'
        flw.completed_notes = request.data.get('notes') or request.data.get('completedNotes', '')
        if request.data.get('nextDate') or request.data.get('next_follow_up_date'):
            flw.next_follow_up_date = request.data.get('nextDate') or request.data.get('next_follow_up_date')
        flw.save()
        return Response(FollowUpSerializer(flw).data)


class SiteVisitViewSet(viewsets.ModelViewSet):
    queryset = SiteVisit.objects.all().order_by('-visit_date')
    serializer_class = SiteVisitSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('visit_no') and not data.get('visitNo'):
            num_setting = NumberingSetting.objects.filter(doc_type='visit').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"VST-2026-{SiteVisit.objects.count() + 1:04d}"
            data['id'] = code
            data['visit_no'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExhibitionViewSet(viewsets.ModelViewSet):
    queryset = Exhibition.objects.all().order_by('-start_date')
    serializer_class = ExhibitionSerializer
    permission_classes = [permissions.AllowAny]


class QuotationViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.all().order_by('-id')
    serializer_class = QuotationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('quotation_number') and not data.get('quotationNumber'):
            num_setting = NumberingSetting.objects.filter(doc_type='quotation').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"QT-2026-{Quotation.objects.count() + 1:04d}"
            data['id'] = code
            data['quotation_number'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='add-revision')
    def add_revision(self, request, pk=None):
        quotation = self.get_object()
        revision_data = request.data.get('revision') or request.data
        revisions = list(quotation.revisions or [])
        revisions.append(revision_data)
        quotation.revisions = revisions
        if revision_data.get('revisionNumber') or revision_data.get('revision_number'):
            quotation.current_revision = revision_data.get('revisionNumber') or revision_data.get('revision_number')
        quotation.save(update_fields=['revisions', 'current_revision'])
        return Response(QuotationSerializer(quotation).data)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        quotation = self.get_object()
        revision_no = request.data.get('revisionNumber') or request.data.get('revision_number')
        new_status = request.data.get('status')
        revisions = list(quotation.revisions or [])
        for r in revisions:
            if (r.get('revisionNumber') == revision_no) or (r.get('revision_number') == revision_no):
                r['status'] = new_status
        quotation.revisions = revisions
        quotation.save(update_fields=['revisions'])
        return Response(QuotationSerializer(quotation).data)


class CustomerPOViewSet(viewsets.ModelViewSet):
    queryset = CustomerPO.objects.all().order_by('-po_date')
    serializer_class = CustomerPOSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id'):
            num_setting = NumberingSetting.objects.filter(doc_type='customer_po').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"CPO-2026-{CustomerPO.objects.count() + 1:04d}"
            data['id'] = code
            data['internal_cpo_no'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert-to-so')
    def convert_to_so(self, request, pk=None):
        po = self.get_object()
        so_num = NumberingSetting.objects.filter(doc_type='sales_order').first()
        so_code = so_num.generate_next_number(increment=True) if so_num else f"SO-2026-{SalesOrder.objects.count() + 1:04d}"

        # Fetch quotation details if linked
        quotation = Quotation.objects.filter(id=po.quotation_id).first() if po.quotation_id else None
        items = []
        tax_amount = 0
        total_amount = po.po_value
        if quotation and quotation.revisions:
            latest_rev = quotation.revisions[-1]
            items = latest_rev.get('items', [])
            total_amount = latest_rev.get('subTotal', po.po_value)
            tax_amount = latest_rev.get('taxAmount', 0)

        so = SalesOrder.objects.create(
            id=so_code,
            sales_order_number=so_code,
            customer_po_id=po.id,
            customer_po_number=po.po_number,
            quotation_id=po.quotation_id,
            quotation_number=po.quotation_number,
            customer_id=po.customer_id,
            customer_name=po.customer_name,
            order_date=datetime.now().strftime('%Y-%m-%d'),
            target_delivery_date=po.delivery_date,
            items=items,
            total_amount=total_amount,
            tax_amount=tax_amount,
            grand_total=po.po_value,
            payment_terms=po.payment_terms,
            status='confirmed',
        )

        po.status = 'converted_to_so'
        po.converted_so_id = so.id
        po.save(update_fields=['status', 'converted_so_id'])

        return Response(SalesOrderSerializer(so).data, status=status.HTTP_201_CREATED)


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all().order_by('-id')
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('sales_order_number') and not data.get('salesOrderNumber'):
            num_setting = NumberingSetting.objects.filter(doc_type='sales_order').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"SO-2026-{SalesOrder.objects.count() + 1:04d}"
            data['id'] = code
            data['sales_order_number'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all().order_by('-created_at')
    serializer_class = ActivitySerializer
    permission_classes = [permissions.AllowAny]
