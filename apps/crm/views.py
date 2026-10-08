from datetime import datetime
from django.db import models
from django.db.models import Q
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
    serializer_class = LeadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Lead.objects.all().order_by('-created_at', '-id')
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(lead_no__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(product_name__icontains=search)
            )
        status_param = self.request.query_params.get('status', '').strip()
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # 1. Map camelCase fields to snake_case
        field_mappings = {
            'leadNo': 'lead_no',
            'leadNumber': 'lead_no',
            'lead_number': 'lead_no',
            'companyName': 'company_name',
            'contactPerson': 'contact_person',
            'altMobile': 'alt_mobile',
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
        }
        for camel, snake in field_mappings.items():
            if camel in data and snake not in data:
                data[snake] = data[camel]

        lead_val = data.get('lead_no') or data.get('lead_number') or data.get('leadNumber') or data.get('leadNo') or data.get('id')
        if lead_val:
            data['lead_no'] = lead_val
            if not data.get('id'):
                data['id'] = lead_val
        else:
            num_setting = NumberingSetting.objects.filter(doc_type='lead').first()
            if num_setting:
                code = num_setting.generate_next_number(increment=True)
                while Lead.objects.filter(id=code).exists() or Lead.objects.filter(lead_no=code).exists():
                    code = num_setting.generate_next_number(increment=True)
            else:
                num = Lead.objects.count() + 1
                code = f"LEAD-2026-{num:04d}"
                while Lead.objects.filter(id=code).exists() or Lead.objects.filter(lead_no=code).exists():
                    num += 1
                    code = f"LEAD-2026-{num:04d}"
            data['id'] = code
            data['lead_no'] = code

        # 2. Check if lead with this exact ID or lead_no already exists in database
        target_id = data.get('id')
        if target_id and not request.data.get('allow_existing'):
            existing = Lead.objects.filter(id=target_id).first() or Lead.objects.filter(lead_no=target_id).first()
            if existing:
                return Response({'error': f"Lead with number '{target_id}' already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if not data.get('created_date'):
            data['created_date'] = datetime.now().strftime('%Y-%m-%d')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert')
    def convert_to_customer(self, request, pk=None):
        lead = self.get_object()

        # 1. Create or retrieve Customer
        num_c = Customer.objects.count() + 1
        while Customer.objects.filter(id=f"CUST-2026-{num_c:04d}").exists() or Customer.objects.filter(customer_code=f"CUST-{num_c:03d}").exists():
            num_c += 1
        cust_code = f"CUST-{num_c:03d}"
        cust_id = f"CUST-2026-{num_c:04d}"

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
        if enq_num:
            enq_code = enq_num.generate_next_number(increment=True)
            while Enquiry.objects.filter(id=enq_code).exists() or Enquiry.objects.filter(enquiry_no=enq_code).exists():
                enq_code = enq_num.generate_next_number(increment=True)
        else:
            num_e = Enquiry.objects.count() + 1
            while Enquiry.objects.filter(id=f"ENQ-2026-{num_e:04d}").exists() or Enquiry.objects.filter(enquiry_no=f"ENQ-2026-{num_e:04d}").exists():
                num_e += 1
            enq_code = f"ENQ-2026-{num_e:04d}"

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
        if opp_num:
            opp_code = opp_num.generate_next_number(increment=True)
            while Opportunity.objects.filter(id=opp_code).exists() or Opportunity.objects.filter(opportunity_no=opp_code).exists():
                opp_code = opp_num.generate_next_number(increment=True)
        else:
            num_o = Opportunity.objects.count() + 1
            while Opportunity.objects.filter(id=f"OPP-2026-{num_o:04d}").exists() or Opportunity.objects.filter(opportunity_no=f"OPP-2026-{num_o:04d}").exists():
                num_o += 1
            opp_code = f"OPP-2026-{num_o:04d}"

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

    @action(detail=False, methods=['get'], url_path='hub-summary')
    def hub_summary(self, request):
        total_leads = Lead.objects.count()
        new_leads = Lead.objects.filter(status='new').count()
        won_leads = Lead.objects.filter(status='won').count()
        total_enquiries = Enquiry.objects.count()
        active_enquiries = Enquiry.objects.exclude(status__in=['closed', 'cancelled']).count()
        total_customers = Customer.objects.count()
        total_pipeline = Lead.objects.aggregate(total=models.Sum('budget'))['total'] or 0
        return Response({
            'total_leads': total_leads,
            'new_leads': new_leads,
            'won_leads': won_leads,
            'total_enquiries': total_enquiries,
            'active_enquiries': active_enquiries,
            'total_customers': total_customers,
            'total_pipeline': total_pipeline,
        })



class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        cust_code = data.get('customer_code') or data.get('customerCode') or data.get('id')
        if not cust_code:
            cnt = Customer.objects.count() + 1
            cust_code = f"CUST-2026-{cnt:04d}"
            while Customer.objects.filter(id=cust_code).exists() or Customer.objects.filter(customer_code=cust_code).exists():
                cnt += 1
                cust_code = f"CUST-2026-{cnt:04d}"
        data['id'] = data.get('id') or cust_code
        data['customer_code'] = data.get('customer_code') or cust_code
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
    queryset = Enquiry.objects.all().order_by('-created_at', '-id')
    serializer_class = EnquirySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        enq_code = data.get('enquiry_no') or data.get('enquiryNo') or data.get('enquiryNumber') or data.get('id')
        if not enq_code:
            num_setting = NumberingSetting.objects.filter(doc_type='enquiry').first()
            enq_code = num_setting.generate_next_number(increment=True) if num_setting else f"ENQ-2026-{Enquiry.objects.count() + 1:04d}"
        data['id'] = data.get('id') or enq_code
        data['enquiry_no'] = enq_code
        if not data.get('enquiry_date') and not data.get('enquiryDate'):
            data['enquiry_date'] = datetime.now().strftime('%Y-%m-%d')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all().order_by('-created_at', '-id')
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
    queryset = FollowUp.objects.all().order_by('-created_at', '-id')
    serializer_class = FollowUpSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('follow_up_no') and not data.get('followUpNo'):
            code = f"FLW-2026-{FollowUp.objects.count() + 1:04d}"
            data['id'] = code
            data['follow_up_no'] = code
        if 'followUpNo' in data and not data.get('follow_up_no'):
            data['follow_up_no'] = data['followUpNo']
        if 'leadOrCustomerId' in data and not data.get('lead_or_customer_id'):
            data['lead_or_customer_id'] = data['leadOrCustomerId']
        if 'leadOrCustomerName' in data and not data.get('lead_or_customer_name'):
            data['lead_or_customer_name'] = data['leadOrCustomerName']
        if 'entityType' in data and not data.get('entity_type'):
            data['entity_type'] = data['entityType']
        if 'assignedToId' in data and not data.get('assigned_to_id'):
            data['assigned_to_id'] = data['assignedToId']
        if 'assignedToName' in data and not data.get('assigned_to_name'):
            data['assigned_to_name'] = data['assignedToName']
        if 'nextFollowUpDate' in data and not data.get('next_follow_up_date'):
            data['next_follow_up_date'] = data['nextFollowUpDate']
        if 'completedNotes' in data and not data.get('completed_notes'):
            data['completed_notes'] = data['completedNotes']
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
    queryset = SiteVisit.objects.all().order_by('-created_at', '-id')
    serializer_class = SiteVisitSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'visitNo' in data and 'visit_no' not in data:
            data['visit_no'] = data['visitNo']
        if 'customerId' in data and 'customer_id' not in data:
            data['customer_id'] = data['customerId']
        if 'customerName' in data and 'customer_name' not in data:
            data['customer_name'] = data['customerName']
        if 'contactPerson' in data and 'contact_person' not in data:
            data['contact_person'] = data['contactPerson']
        if 'contactMobile' in data and 'contact_mobile' not in data:
            data['contact_mobile'] = data['contactMobile']
        if 'visitDate' in data and 'visit_date' not in data:
            data['visit_date'] = data['visitDate']
        if 'employeeId' in data and 'employee_id' not in data:
            data['employee_id'] = data['employeeId']
        if 'employeeName' in data and 'employee_name' not in data:
            data['employee_name'] = data['employeeName']
        if 'discussionNotes' in data and 'discussion_notes' not in data:
            data['discussion_notes'] = data['discussionNotes']
        elif 'discussionSummary' in data and 'discussion_notes' not in data:
            data['discussion_notes'] = data['discussionSummary']
        if 'requirementDetails' in data and 'requirement_details' not in data:
            data['requirement_details'] = data['requirementDetails']
        if 'nextAction' in data and 'next_action' not in data:
            data['next_action'] = data['nextAction']
        if 'nextFollowUpDate' in data and 'next_follow_up_date' not in data:
            data['next_follow_up_date'] = data['nextFollowUpDate']

        if not data.get('id'):
            data['id'] = data.get('visit_no') or data.get('visitNo')
        if not data.get('id') or not data.get('visit_no'):
            num_setting = NumberingSetting.objects.filter(doc_type='visit').first()
            code = num_setting.generate_next_number(increment=True) if num_setting else f"VST-2026-{SiteVisit.objects.count() + 1:04d}"
            data['id'] = code
            data['visit_no'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExhibitionViewSet(viewsets.ModelViewSet):
    queryset = Exhibition.objects.all().order_by('-created_at', '-id')
    serializer_class = ExhibitionSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'expoName' in data and 'expo_name' not in data:
            data['expo_name'] = data['expoName']
        if 'startDate' in data and 'start_date' not in data:
            data['start_date'] = data['startDate']
        if 'endDate' in data and 'end_date' not in data:
            data['end_date'] = data['endDate']
        if 'stallNumber' in data and 'stall_number' not in data:
            data['stall_number'] = data['stallNumber']
        if 'contactPerson' in data and 'contact_person' not in data:
            data['contact_person'] = data['contactPerson']
        if 'assignedTeam' in data and 'assigned_team' not in data:
            data['assigned_team'] = data['assignedTeam']
        if 'productsDisplayed' in data and 'products_displayed' not in data:
            data['products_displayed'] = data['productsDisplayed']
        if 'totalContacts' in data and 'total_contacts' not in data:
            data['total_contacts'] = data['totalContacts']
        if 'qualifiedLeads' in data and 'qualified_leads' not in data:
            data['qualified_leads'] = data['qualifiedLeads']
        if 'quotationsSent' in data and 'quotations_sent' not in data:
            data['quotations_sent'] = data['quotationsSent']
        if 'convertedCustomers' in data and 'converted_customers' not in data:
            data['converted_customers'] = data['convertedCustomers']

        if not data.get('id'):
            code = f"EXPO-2026-{Exhibition.objects.count() + 1:02d}"
            data['id'] = code

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuotationViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.all().order_by('-created_at', '-id')
    serializer_class = QuotationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        quo_num = data.get('quotation_number') or data.get('quotationNumber') or data.get('id')
        if not quo_num or Quotation.objects.filter(id=quo_num).exists():
            import re
            all_ids = list(Quotation.objects.values_list('id', flat=True))
            max_num = 0
            for qid in all_ids:
                match = re.search(r'(\d+)$', str(qid))
                if match:
                    max_num = max(max_num, int(match.group(1)))
            num_setting = NumberingSetting.objects.filter(doc_type='quotation').first()
            prefix = num_setting.prefix if num_setting else "QT-2026-"
            digit_count = getattr(num_setting, 'digit_count', getattr(num_setting, 'digitCount', 4)) if num_setting else 4
            next_num = max(max_num + 1, (num_setting.current_number + 1 if num_setting else 1))
            quo_num = f"{prefix}{next_num:0{digit_count}d}"
            while Quotation.objects.filter(id=quo_num).exists():
                next_num += 1
                quo_num = f"{prefix}{next_num:0{digit_count}d}"
            if num_setting:
                num_setting.current_number = next_num
                num_setting.save(update_fields=['current_number'])
        data['id'] = quo_num
        data['quotation_number'] = quo_num

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Update linked enquiry if provided
        enq_id = data.get('enquiry_id') or data.get('enquiryId')
        cust_id = data.get('customer_id') or data.get('customerId')
        if enq_id:
            Enquiry.objects.filter(models.Q(id=enq_id) | models.Q(enquiry_no=enq_id)).update(
                quotation_id=quo_num,
                status='quotation_sent'
            )
            Lead.objects.filter(converted_enquiry_id=enq_id).update(
                status='quotation_sent'
            )
        elif cust_id:
            Enquiry.objects.filter(customer_id=cust_id, quotation_id__isnull=True).update(
                quotation_id=quo_num,
                status='quotation_sent'
            )
            Lead.objects.filter(converted_customer_id=cust_id).update(
                status='quotation_sent'
            )

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
        matched = False
        for r in revisions:
            if not revision_no or (r.get('revisionNumber') == revision_no) or (r.get('revision_number') == revision_no):
                r['status'] = new_status
                matched = True
        if not matched and revisions:
            revisions[-1]['status'] = new_status
        quotation.revisions = revisions
        quotation.save(update_fields=['revisions'])
        return Response(QuotationSerializer(quotation).data)


class CustomerPOViewSet(viewsets.ModelViewSet):
    queryset = CustomerPO.objects.all().order_by('-created_at', '-id')
    serializer_class = CustomerPOSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        po_num = data.get('po_number') or data.get('poNumber')
        cpo_id = data.get('id') or data.get('internal_cpo_no') or data.get('internalCpoNo')
        
        # Ensure a truly unique fresh ID so existing records are NEVER overwritten on create
        if not cpo_id or CustomerPO.objects.filter(id=cpo_id).exists():
            import re
            all_ids = list(CustomerPO.objects.values_list('id', flat=True))
            max_num = 0
            for cid in all_ids:
                match = re.search(r'(\d+)$', str(cid))
                if match:
                    max_num = max(max_num, int(match.group(1)))
            num_setting = NumberingSetting.objects.filter(doc_type='customer_po').first()
            prefix = num_setting.prefix if num_setting else "CPO-2026-"
            digit_count = getattr(num_setting, 'digit_count', getattr(num_setting, 'digitCount', 4)) if num_setting else 4
            next_num = max(max_num + 1, (num_setting.current_number + 1 if num_setting else 1))
            cpo_id = f"{prefix}{next_num:0{digit_count}d}"
            while CustomerPO.objects.filter(id=cpo_id).exists():
                next_num += 1
                cpo_id = f"{prefix}{next_num:0{digit_count}d}"
            if num_setting:
                num_setting.current_number = next_num
                num_setting.save(update_fields=['current_number'])

        data['id'] = cpo_id
        data['internal_cpo_no'] = cpo_id
        if po_num:
            data['po_number'] = po_num
        if not data.get('received_date') and not data.get('receivedDate'):
            data['received_date'] = data.get('po_date') or data.get('poDate') or datetime.now().strftime('%Y-%m-%d')
        if not data.get('po_value') and not data.get('poValue'):
            data['po_value'] = data.get('poAmount') or data.get('po_amount') or 0

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert-to-so')
    def convert_to_so(self, request, pk=None):
        po = self.get_object()
        so_num = NumberingSetting.objects.filter(doc_type='sales_order').first()
        so_code = so_num.generate_next_number(increment=True) if so_num else f"SO-2026-{SalesOrder.objects.count() + 1:04d}"
        while SalesOrder.objects.filter(id=so_code).exists():
            so_code = f"SO-2026-{SalesOrder.objects.count() + 1:04d}-{datetime.now().strftime('%M%S')}"

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

        if not items:
            items = [
                {
                    'id': 'so-item-1',
                    'productName': f"Custom Equipment (Ref {po.quotation_number or po.po_number})",
                    'specification': po.scope_of_work or 'As per approved Quotation & Customer PO specs',
                    'quantity': 1,
                    'unit': 'Set',
                    'rate': po.po_value,
                    'amount': po.po_value,
                }
            ]

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
            target_delivery_date=po.delivery_date or datetime.now().strftime('%Y-%m-%d'),
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
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_val = self.kwargs.get(lookup_url_kwarg)
        obj = queryset.filter(id=lookup_val).first() or queryset.filter(sales_order_number=lookup_val).first()
        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Sales order '{lookup_val}' not found.")
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        try:
            # Clean up and merge any stray DOC- sales orders into real SO-2026- records
            doc_orders = list(SalesOrder.objects.filter(id__startswith='DOC-'))
            for doc_so in doc_orders:
                c_name = doc_so.customer_name
                po_ref = doc_so.customer_po_number
                matching_so = None
                if c_name and po_ref:
                    matching_so = SalesOrder.objects.filter(
                        customer_name=c_name,
                        customer_po_number=po_ref
                    ).exclude(id=doc_so.id).first()
                if matching_so:
                    changed = False
                    if doc_so.project_id and not matching_so.project_id:
                        matching_so.project_id = doc_so.project_id
                        changed = True
                    if doc_so.status == 'project_created' and matching_so.status != 'project_created':
                        matching_so.status = 'project_created'
                        changed = True
                    if changed:
                        matching_so.save()
                    doc_so.delete()
        except Exception:
            pass
        return SalesOrder.objects.all().order_by('-created_at', '-id')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        cust_name = data.get('customer_name') or data.get('customerName')
        po_num = data.get('customer_po_number') or data.get('customerPoNumber')
        if cust_name and po_num:
            existing = SalesOrder.objects.filter(customer_name=cust_name, customer_po_number=po_num).first()
            if existing:
                serializer = self.get_serializer(existing, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

        so_num = data.get('sales_order_number') or data.get('salesOrderNumber') or data.get('id')
        if not so_num or SalesOrder.objects.filter(id=so_num).exists():
            import re
            all_ids = list(SalesOrder.objects.values_list('id', flat=True))
            max_num = 0
            for soid in all_ids:
                match = re.search(r'(\d+)$', str(soid))
                if match:
                    max_num = max(max_num, int(match.group(1)))
            num_setting = NumberingSetting.objects.filter(doc_type='sales_order').first()
            prefix = num_setting.prefix if num_setting else "SO-2026-"
            digit_count = getattr(num_setting, 'digit_count', getattr(num_setting, 'digitCount', 4)) if num_setting else 4
            next_num = max(max_num + 1, (num_setting.current_number + 1 if num_setting else 1))
            so_num = f"{prefix}{next_num:0{digit_count}d}"
            while SalesOrder.objects.filter(id=so_num).exists():
                next_num += 1
                so_num = f"{prefix}{next_num:0{digit_count}d}"
            if num_setting:
                num_setting.current_number = next_num
                num_setting.save(update_fields=['current_number'])
        data['id'] = so_num
        data['sales_order_number'] = so_num
        if not data.get('target_delivery_date') and not data.get('targetDeliveryDate'):
            data['target_delivery_date'] = data.get('deliveryDate') or data.get('delivery_date') or datetime.now().strftime('%Y-%m-%d')
        if not data.get('order_date') and not data.get('orderDate'):
            data['order_date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('grand_total') and not data.get('grandTotal'):
            data['grand_total'] = data.get('orderValue') or data.get('totalAmount') or 0
        if not data.get('total_amount') and not data.get('totalAmount'):
            data['total_amount'] = data.get('orderValue') or data.get('grandTotal') or 0

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all().order_by('-created_at')
    serializer_class = ActivitySerializer
    permission_classes = [permissions.AllowAny]

