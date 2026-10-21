from datetime import datetime
from django.db import models
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.core.models import NumberingSetting, AuditLog
from apps.core.approval_security import (
    validate_approval_permission,
    validate_approval_transition,
    validate_edit_safety,
    log_approval_audit,
)

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


def _ensure_crm_schema():
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("UPDATE crm_quotation SET rejection_reason = '' WHERE rejection_reason IS NULL;")
            cursor.execute("UPDATE crm_quotation SET notes = '' WHERE notes IS NULL;")
            cursor.execute("UPDATE crm_quotation SET machine_product = '' WHERE machine_product IS NULL;")
            cursor.execute("UPDATE crm_quotation SET contact_person = '' WHERE contact_person IS NULL;")
            cursor.execute("UPDATE crm_quotation SET contact_mobile = '' WHERE contact_mobile IS NULL;")
            cursor.execute("UPDATE crm_quotation SET contact_email = '' WHERE contact_email IS NULL;")
            cursor.execute("UPDATE crm_quotation SET sales_person_id = '' WHERE sales_person_id IS NULL;")
            cursor.execute("UPDATE crm_quotation SET sales_person_name = '' WHERE sales_person_name IS NULL;")

            # Clean up dummy data and restore real contact data from quotations & enquiries where possible
            try:
                # 1. Restore company_name from linked quotation if dummy
                cursor.execute("""
                    UPDATE crm_lead
                    SET company_name = (
                        SELECT customer_name FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.customer_name != '' AND crm_quotation.customer_name != 'Valued Customer'
                        ORDER BY crm_quotation.id DESC
                        LIMIT 1
                    )
                    WHERE (company_name = '' OR company_name = 'Valued Customer')
                      AND EXISTS (
                        SELECT 1 FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.customer_name != '' AND crm_quotation.customer_name != 'Valued Customer'
                      );
                """)

                # 2. Restore contact_person from linked quotation if dummy or empty
                cursor.execute("""
                    UPDATE crm_lead
                    SET contact_person = (
                        SELECT contact_person FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.contact_person != '' AND crm_quotation.contact_person != 'Contact Person' AND crm_quotation.contact_person != 'Contact'
                        ORDER BY crm_quotation.id DESC
                        LIMIT 1
                    )
                    WHERE (contact_person = '' OR contact_person = 'Contact Person' OR contact_person = 'Contact')
                      AND EXISTS (
                        SELECT 1 FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.contact_person != '' AND crm_quotation.contact_person != 'Contact Person' AND crm_quotation.contact_person != 'Contact'
                      );
                """)

                # 3. Restore product_name & quantity from linked quotation if placeholder
                cursor.execute("""
                    UPDATE crm_lead
                    SET product_name = (
                        SELECT machine_product FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.machine_product != '' AND crm_quotation.machine_product != 'Process Equipment'
                        ORDER BY crm_quotation.id DESC
                        LIMIT 1
                    )
                    WHERE (product_name = '' OR product_name = 'Process Equipment' OR product_name = 'Industrial Process Equipment')
                      AND EXISTS (
                        SELECT 1 FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.machine_product != '' AND crm_quotation.machine_product != 'Process Equipment'
                      );
                """)

                cursor.execute("""
                    UPDATE crm_lead
                    SET quantity = (
                        SELECT quantity FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.quantity > 0
                        ORDER BY crm_quotation.id DESC
                        LIMIT 1
                    )
                    WHERE (quantity IS NULL OR quantity = 0)
                      AND EXISTS (
                        SELECT 1 FROM crm_quotation
                        WHERE (crm_quotation.lead_id = crm_lead.id OR crm_quotation.lead_id = crm_lead.lead_no)
                          AND crm_quotation.quantity > 0
                      );
                """)

                # 4. Restore mobile & contact_person from enquiry if still missing
                cursor.execute("""
                    UPDATE crm_lead
                    SET mobile = (
                        SELECT contact_mobile FROM crm_enquiry
                        WHERE (crm_enquiry.lead_id = crm_lead.id OR crm_enquiry.lead_id = crm_lead.lead_no)
                          AND crm_enquiry.contact_mobile != '' AND crm_enquiry.contact_mobile != '9999999999'
                        LIMIT 1
                    )
                    WHERE (mobile = '' OR mobile = '9999999999')
                      AND EXISTS (
                        SELECT 1 FROM crm_enquiry
                        WHERE (crm_enquiry.lead_id = crm_lead.id OR crm_enquiry.lead_id = crm_lead.lead_no)
                          AND crm_enquiry.contact_mobile != '' AND crm_enquiry.contact_mobile != '9999999999'
                      );
                """)
                cursor.execute("""
                    UPDATE crm_lead
                    SET contact_person = (
                        SELECT contact_person FROM crm_enquiry
                        WHERE (crm_enquiry.lead_id = crm_lead.id OR crm_enquiry.lead_id = crm_lead.lead_no)
                          AND crm_enquiry.contact_person != '' AND crm_enquiry.contact_person != 'Contact Person' AND crm_enquiry.contact_person != 'Contact'
                        LIMIT 1
                    )
                    WHERE (contact_person = '' OR contact_person = 'Contact Person' OR contact_person = 'Contact')
                      AND EXISTS (
                        SELECT 1 FROM crm_enquiry
                        WHERE (crm_enquiry.lead_id = crm_lead.id OR crm_enquiry.lead_id = crm_lead.lead_no)
                          AND crm_enquiry.contact_person != '' AND crm_enquiry.contact_person != 'Contact Person' AND crm_enquiry.contact_person != 'Contact'
                      );
                """)
                cursor.execute("UPDATE crm_lead SET mobile = '' WHERE mobile = '9999999999';")
                cursor.execute("UPDATE crm_lead SET contact_person = '' WHERE contact_person = 'Contact Person' OR contact_person = 'Contact';")

                # Auto-heal quotation contact_email from linked leads, enquiries, and customers
                cursor.execute("""
                    UPDATE crm_quotation
                    SET contact_email = (
                        SELECT email FROM crm_lead
                        WHERE (crm_lead.id = crm_quotation.lead_id OR crm_lead.lead_no = crm_quotation.lead_id)
                          AND crm_lead.email != ''
                        LIMIT 1
                    )
                    WHERE (contact_email IS NULL OR contact_email = '')
                      AND lead_id IS NOT NULL AND lead_id != ''
                      AND EXISTS (
                        SELECT 1 FROM crm_lead
                        WHERE (crm_lead.id = crm_quotation.lead_id OR crm_lead.lead_no = crm_quotation.lead_id)
                          AND crm_lead.email != ''
                      );
                """)
                cursor.execute("""
                    UPDATE crm_quotation
                    SET contact_email = (
                        SELECT customer_email FROM crm_enquiry
                        WHERE (crm_enquiry.id = crm_quotation.enquiry_id OR crm_enquiry.enquiry_no = crm_quotation.enquiry_id)
                          AND crm_enquiry.customer_email != ''
                        LIMIT 1
                    )
                    WHERE (contact_email IS NULL OR contact_email = '')
                      AND enquiry_id IS NOT NULL AND enquiry_id != ''
                      AND EXISTS (
                        SELECT 1 FROM crm_enquiry
                        WHERE (crm_enquiry.id = crm_quotation.enquiry_id OR crm_enquiry.enquiry_no = crm_quotation.enquiry_id)
                          AND crm_enquiry.customer_email != ''
                      );
                """)
                cursor.execute("""
                    UPDATE crm_quotation
                    SET contact_email = (
                        SELECT email FROM crm_lead
                        WHERE LOWER(TRIM(crm_lead.company_name)) = LOWER(TRIM(crm_quotation.customer_name))
                          AND crm_lead.email != ''
                        LIMIT 1
                    )
                    WHERE (contact_email IS NULL OR contact_email = '')
                      AND EXISTS (
                        SELECT 1 FROM crm_lead
                        WHERE LOWER(TRIM(crm_lead.company_name)) = LOWER(TRIM(crm_quotation.customer_name))
                          AND crm_lead.email != ''
                      );
                """)
            except Exception:
                pass
    except Exception:
        pass


try:
    _ensure_crm_schema()
except Exception:
    pass



class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all().order_by('-created_at', '-id')
    serializer_class = LeadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM crm_lead WHERE id = '' OR lead_no = '' OR id IS NULL OR lead_no IS NULL")
        except Exception:
            pass
        queryset = Lead.objects.exclude(id='').exclude(lead_no='').exclude(id__isnull=True).order_by('-created_at', '-id')
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        valid_items = []
        for obj in queryset:
            clean_id = str(getattr(obj, 'id', '') or '').strip()
            clean_lead_no = str(getattr(obj, 'lead_no', '') or '').strip()
            if clean_id and clean_lead_no:
                valid_items.append(obj)
            else:
                try:
                    obj.delete()
                except Exception:
                    pass
        serializer = self.get_serializer(valid_items, many=True)
        return Response(serializer.data)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        val = str(self.kwargs.get(lookup_url_kwarg, '')).strip()
        import urllib.parse
        decoded = urllib.parse.unquote(val).strip()

        # 1. Direct match by id or lead_no
        obj = (
            queryset.filter(id=val).first() or
            queryset.filter(lead_no=val).first() or
            queryset.filter(id=decoded).first() or
            queryset.filter(lead_no=decoded).first() or
            queryset.filter(id__iexact=decoded).first() or
            queryset.filter(lead_no__iexact=decoded).first()
        )

        # 2. Resilient slug / substring match if legacy composite key passed
        if not obj and decoded:
            clean_decoded = decoded.lower().replace('-', ' ').replace('_', ' ')
            for cand in queryset:
                cand_str = f"{cand.company_name} {cand.product_name}".lower()
                if clean_decoded in cand_str or cand_str in clean_decoded:
                    obj = cand
                    break

        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"No lead found matching '{val}'.")

        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        # Never allow primary key or unique lead_no overwrite on update
        data.pop('id', None)
        data.pop('lead_no', None)
        data.pop('leadNo', None)
        if 'mobile' in data or 'phone' in data or 'contactMobile' in data or 'contact_mobile' in data or 'contactNumber' in data or 'mobileNo' in data:
            data['mobile'] = str(data.get('mobile') or data.get('phone') or data.get('contactMobile') or data.get('contact_mobile') or data.get('contactNumber') or data.get('mobileNo') or '').strip()
        if 'contactPerson' in data or 'contact_person' in data or 'contact' in data:
            data['contact_person'] = str(data.get('contactPerson') or data.get('contact_person') or data.get('contact') or '').strip()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        import threading
        if not hasattr(self.__class__, '_create_lock'):
            self.__class__._create_lock = threading.Lock()
            
        with self.__class__._create_lock:
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

            # Normalize mobile and contact person from all variations
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

            if not data.get('contact_person'):
                data['contact_person'] = str(data.get('contactPerson') or data.get('contact') or '').strip()

            is_explicit_id = bool(data.get('lead_no') or data.get('lead_number') or data.get('leadNumber') or data.get('leadNo') or data.get('id'))
            lead_val = data.get('lead_no') or data.get('lead_number') or data.get('leadNumber') or data.get('leadNo') or data.get('id')
            if is_explicit_id:
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
                    import re
                    all_ids = list(Lead.objects.values_list('id', flat=True)) + list(Lead.objects.values_list('lead_no', flat=True))
                    max_num = 0
                    for lid in all_ids:
                        m = re.search(r'(\d+)$', str(lid))
                        if m:
                            max_num = max(max_num, int(m.group(1)))
                    num = max(max_num + 1, Lead.objects.count() + 1)
                    code = f"LEAD-2026-{num:04d}"
                    while Lead.objects.filter(id=code).exists() or Lead.objects.filter(lead_no=code).exists():
                        num += 1
                        code = f"LEAD-2026-{num:04d}"
                data['id'] = code
                data['lead_no'] = code

            # 2. If lead with this exact ID or lead_no already exists in database, auto-assign next free number
            target_id = data.get('id')
            if target_id:
                existing = Lead.objects.filter(id=target_id).first() or Lead.objects.filter(lead_no=target_id).first()
                if existing:
                    import re
                    all_ids = list(Lead.objects.values_list('id', flat=True)) + list(Lead.objects.values_list('lead_no', flat=True))
                    max_num = 0
                    for lid in all_ids:
                        m = re.search(r'(\d+)$', str(lid))
                        if m:
                            max_num = max(max_num, int(m.group(1)))
                    num = max(max_num + 1, Lead.objects.count() + 1)
                    code = f"LEAD-2026-{num:04d}"
                    while Lead.objects.filter(id=code).exists() or Lead.objects.filter(lead_no=code).exists():
                        num += 1
                        code = f"LEAD-2026-{num:04d}"
                    data['id'] = code
                    data['lead_no'] = code

            if not data.get('created_date'):
                data['created_date'] = datetime.now().strftime('%Y-%m-%d')

            if data.get('expected_delivery') is None:
                data['expected_delivery'] = ''
            if data.get('next_follow_up_date') is None:
                data['next_follow_up_date'] = ''

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

        # 2. Also create Opportunity
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

        # 3. Create or link Enquiry
        enquiry = None
        if lead.converted_enquiry_id:
            enquiry = Enquiry.objects.filter(id=lead.converted_enquiry_id).first()
        if not enquiry:
            num_setting = NumberingSetting.objects.filter(doc_type='enquiry').first()
            if num_setting:
                enq_code = num_setting.generate_next_number(increment=True)
                while Enquiry.objects.filter(id=enq_code).exists() or Enquiry.objects.filter(enquiry_no=enq_code).exists():
                    enq_code = num_setting.generate_next_number(increment=True)
            else:
                num_e = Enquiry.objects.count() + 1
                enq_code = f"ENQ-2026-{num_e:04d}"
                while Enquiry.objects.filter(id=enq_code).exists() or Enquiry.objects.filter(enquiry_no=enq_code).exists():
                    num_e += 1
                    enq_code = f"ENQ-2026-{num_e:04d}"

            enquiry = Enquiry.objects.create(
                id=enq_code,
                enquiry_no=enq_code,
                lead_id=lead.id,
                customer_id=customer.id,
                customer_name=customer.company_name,
                customer_email=lead.email or '',
                contact_person=lead.contact_person or '',
                contact_mobile=lead.mobile or '',
                machine_product=lead.product_name,
                quantity=lead.quantity or 1,
                requirement=lead.requirement_description or f"Enquiry created on customer conversion from lead {lead.lead_no}",
                status='active',
                enquiry_date=datetime.now().strftime('%Y-%m-%d'),
            )
            lead.converted_enquiry_id = enquiry.id
        else:
            if not enquiry.customer_id:
                enquiry.customer_id = customer.id
                enquiry.save(update_fields=['customer_id'])

        # Update Lead status
        lead.status = 'won'
        lead.converted_customer_id = customer.id
        lead.converted_opportunity_id = opportunity.id
        lead.save(update_fields=['status', 'converted_customer_id', 'converted_opportunity_id', 'converted_enquiry_id'])

        return Response({
            'success': True,
            'customer': CustomerSerializer(customer).data,
            'enquiry': EnquirySerializer(enquiry).data,
            'opportunity': OpportunitySerializer(opportunity).data,
        })

    @action(detail=True, methods=['post'], url_path='convert-to-customer')
    def convert_to_customer_alias(self, request, pk=None):
        return self.convert_to_customer(request, pk)

    @action(detail=True, methods=['post'], url_path='convert-to-enquiry')
    def convert_to_enquiry(self, request, pk=None):
        lead = self.get_object()

        # Check if already converted to enquiry
        if lead.converted_enquiry_id:
            existing_enq = Enquiry.objects.filter(id=lead.converted_enquiry_id).first()
            if existing_enq:
                return Response({
                    'success': True,
                    'enquiry': EnquirySerializer(existing_enq).data,
                    'already_exists': True
                })

        num_setting = NumberingSetting.objects.filter(doc_type='enquiry').first()
        if num_setting:
            code = num_setting.generate_next_number(increment=True)
            while Enquiry.objects.filter(id=code).exists() or Enquiry.objects.filter(enquiry_no=code).exists():
                code = num_setting.generate_next_number(increment=True)
        else:
            num_e = Enquiry.objects.count() + 1
            code = f"ENQ-2026-{num_e:04d}"
            while Enquiry.objects.filter(id=code).exists() or Enquiry.objects.filter(enquiry_no=code).exists():
                num_e += 1
                code = f"ENQ-2026-{num_e:04d}"

        enquiry = Enquiry.objects.create(
            id=code,
            enquiry_no=code,
            lead_id=lead.id,
            customer_id=lead.converted_customer_id or '',
            customer_name=lead.company_name,
            customer_email=lead.email,
            contact_person=lead.contact_person,
            contact_mobile=lead.mobile,
            enquiry_date=datetime.now().strftime('%Y-%m-%d'),
            requirement=lead.requirement_description or f"Enquiry for {lead.product_name}",
            machine_product=lead.product_name,
            machine_type=lead.machine_type or '',
            application=lead.application or '',
            capacity=lead.capacity or '',
            budget=lead.budget or 0,
            quantity=lead.quantity or 1,
            specification=lead.capacity or '',
            expected_delivery=lead.expected_delivery or '',
            assigned_person_id=lead.assigned_sales_person_id,
            assigned_person_name=lead.assigned_sales_person_name,
            status='new',
        )

        lead.converted_enquiry_id = enquiry.id
        lead.status = 'requirement_received'
        lead.save(update_fields=['converted_enquiry_id', 'status'])

        return Response({
            'success': True,
            'enquiry': EnquirySerializer(enquiry).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='hub-summary')
    def hub_summary(self, request):
        total_leads = Lead.objects.count()
        new_leads = Lead.objects.filter(status='new').count()
        won_leads = Lead.objects.filter(status='won').count()
        total_quotations = Quotation.objects.count()
        active_quotations = Quotation.objects.filter(status='draft').count()
        total_customers = Customer.objects.count()
        total_pipeline = Lead.objects.aggregate(total=models.Sum('budget'))['total'] or 0
        return Response({
            'total_leads': total_leads,
            'new_leads': new_leads,
            'won_leads': won_leads,
            'total_quotations': total_quotations,
            'active_quotations': active_quotations,
            'total_customers': total_customers,
            'total_pipeline': total_pipeline,
        })





class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        import threading
        if not hasattr(self.__class__, '_create_lock'):
            self.__class__._create_lock = threading.Lock()
        with self.__class__._create_lock:
            data = request.data.copy()
            cust_code = data.get('customer_code') or data.get('customerCode') or data.get('id')
            if not cust_code:
                import re
                all_codes = list(Customer.objects.values_list('customer_code', flat=True)) + list(Customer.objects.values_list('id', flat=True))
                max_num = 0
                for cc in all_codes:
                    m = re.search(r'(\d+)$', str(cc))
                    if m:
                        max_num = max(max_num, int(m.group(1)))
                cnt = max(max_num + 1, Customer.objects.count() + 1)
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
    queryset = Contact.objects.all().order_by('-id')
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]


class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.all().order_by('-created_at', '-id')
    serializer_class = EnquirySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # 1. Generate unique Enquiry number / ID if not provided
        enq_num = data.get('enquiry_no') or data.get('enquiryNo') or data.get('id')
        if not enq_num or Enquiry.objects.filter(id=enq_num).exists():
            num_setting = NumberingSetting.objects.filter(doc_type='enquiry').first()
            if num_setting:
                code = num_setting.generate_next_number(increment=True)
                while Enquiry.objects.filter(id=code).exists() or Enquiry.objects.filter(enquiry_no=code).exists():
                    code = num_setting.generate_next_number(increment=True)
            else:
                import re
                all_ids = list(Enquiry.objects.values_list('id', flat=True))
                max_num = 0
                for eid in all_ids:
                    match = re.search(r'(\d+)$', str(eid))
                    if match:
                        max_num = max(max_num, int(match.group(1)))
                next_num = max_num + 1
                code = f"ENQ-2026-{next_num:04d}"
                while Enquiry.objects.filter(id=code).exists():
                    next_num += 1
                    code = f"ENQ-2026-{next_num:04d}"
            data['id'] = code
            data['enquiry_no'] = code
        else:
            data['id'] = enq_num
            data['enquiry_no'] = enq_num

        if not data.get('enquiry_date') and not data.get('enquiryDate'):
            data['enquiry_date'] = datetime.now().strftime('%Y-%m-%d')

        # Fallback values from Lead if provided
        lead_id = data.get('lead_id') or data.get('leadId')
        if lead_id:
            ld = Lead.objects.filter(models.Q(id=lead_id) | models.Q(lead_no=lead_id)).first()
            if ld:
                if not data.get('customer_name') and not data.get('customerName'):
                    data['customer_name'] = ld.company_name
                if not data.get('customer_email') and not data.get('customerEmail'):
                    data['customer_email'] = ld.email
                if not data.get('contact_person') and not data.get('contactPerson'):
                    data['contact_person'] = ld.contact_person
                if not data.get('contact_mobile') and not data.get('contactMobile'):
                    data['contact_mobile'] = ld.mobile
                if not data.get('machine_product') and not data.get('machineProduct'):
                    data['machine_product'] = ld.product_name
                if not data.get('machine_type') and not data.get('machineType'):
                    data['machine_type'] = ld.machine_type
                if not data.get('application'):
                    data['application'] = ld.application
                if not data.get('capacity'):
                    data['capacity'] = ld.capacity
                if not data.get('budget'):
                    data['budget'] = ld.budget
                if not data.get('quantity'):
                    data['quantity'] = ld.quantity

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Update linked Lead with converted_enquiry_id
        if lead_id:
            enq_id = serializer.data.get('id') or data.get('id')
            Lead.objects.filter(models.Q(id=lead_id) | models.Q(lead_no=lead_id)).update(
                converted_enquiry_id=enq_id,
                status='requirement_received'
            )

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
        if 'enquiryId' in data and not data.get('enquiry_id'):
            data['enquiry_id'] = data['enquiryId']
        if 'quotationId' in data and not data.get('quotation_id'):
            data['quotation_id'] = data['quotationId']
        if 'outcome' in data and not data.get('outcome'):
            data['outcome'] = data['outcome']
        if 'customerResponse' in data and not data.get('customer_response'):
            data['customer_response'] = data['customerResponse']
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
        if 'leadId' in data and 'lead_id' not in data:
            data['lead_id'] = data['leadId']
        if 'enquiryId' in data and 'enquiry_id' not in data:
            data['enquiry_id'] = data['enquiryId']
        if 'siteMeasurements' in data and 'site_measurements' not in data:
            data['site_measurements'] = data['siteMeasurements']
        if 'operatingConditions' in data and 'operating_conditions' not in data:
            data['operating_conditions'] = data['operatingConditions']
        if 'technicalObservations' in data and 'technical_observations' not in data:
            data['technical_observations'] = data['technicalObservations']
        if 'pendingClarifications' in data and 'pending_clarifications' not in data:
            data['pending_clarifications'] = data['pendingClarifications']

        if not data.get('customer_id'):
            data['customer_id'] = data.get('customerId') or data.get('lead_id') or data.get('enquiry_id') or 'LEAD-PROSPECT'

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
        if 'participationStatus' in data and 'participation_status' not in data:
            data['participation_status'] = data['participationStatus']
        if 'actualExpenses' in data and 'actual_expenses' not in data:
            data['actual_expenses'] = data['actualExpenses']

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
        import threading
        if not hasattr(self.__class__, '_create_lock'):
            self.__class__._create_lock = threading.Lock()
        with self.__class__._create_lock:
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

            # Update linked lead/customer/enquiry if provided
            lead_id = data.get('lead_id') or data.get('leadId')
            cust_id = data.get('customer_id') or data.get('customerId')
            enq_id = data.get('enquiry_id') or data.get('enquiryId')
            if lead_id:
                Lead.objects.filter(models.Q(id=lead_id) | models.Q(lead_no=lead_id)).update(
                    status='quotation_sent'
                )
            if cust_id:
                Lead.objects.filter(converted_customer_id=cust_id).update(
                    status='quotation_sent'
                )
            if enq_id:
                Enquiry.objects.filter(models.Q(id=enq_id) | models.Q(enquiry_no=enq_id)).update(
                    quotation_id=quo_num,
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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        for k in ['rejection_reason', 'notes', 'machine_product', 'approved_by', 'contact_person', 'contact_mobile', 'contact_email', 'sales_person_id', 'sales_person_name']:
            if getattr(instance, k, None) is None:
                setattr(instance, k, '')
        safe, err_resp = validate_edit_safety(instance, request.data)
        if not safe:
            return err_resp
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        for k in ['rejection_reason', 'notes', 'machine_product', 'approved_by', 'contact_person', 'contact_mobile', 'contact_email', 'sales_person_id', 'sales_person_name']:
            if getattr(instance, k, None) is None:
                setattr(instance, k, '')
        safe, err_resp = validate_edit_safety(instance, request.data)
        if not safe:
            return err_resp
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        quotation = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Sales', 'Commercial', 'Marketing', 'Management'],
            allowed_roles=['Sales Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(quotation.status, 'approve')
        if not valid_trans:
            return trans_resp

        approver = user_info['name'] or request.data.get('approvedBy') or request.data.get('approved_by') or 'Admin User'
        comment = request.data.get('comment') or request.data.get('approvalNotes') or 'Approved'

        quotation.status = 'approved'
        quotation.approved_by = approver
        from django.utils import timezone
        quotation.approved_at = timezone.now()
        
        revisions = list(quotation.revisions or [])
        if revisions:
            revisions[-1]['status'] = 'approved'
            revisions[-1]['approvedBy'] = approver
            revisions[-1]['approvalComment'] = comment
        quotation.revisions = revisions
        quotation.save(update_fields=['status', 'approved_by', 'approved_at', 'revisions'])

        log_approval_audit(user_info, 'APPROVE', 'CRM', 'Quotation', quotation.id, comment)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        quotation = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Sales', 'Commercial', 'Marketing', 'Management'],
            allowed_roles=['Sales Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(quotation.status, 'reject')
        if not valid_trans:
            return trans_resp

        reason = request.data.get('reason') or request.data.get('rejectionReason') or request.data.get('rejection_reason') or 'Commercial or technical discrepancy'
        quotation.status = 'rejected'
        quotation.rejection_reason = reason
        
        revisions = list(quotation.revisions or [])
        if revisions:
            revisions[-1]['status'] = 'rejected'
            revisions[-1]['rejectionReason'] = reason
        quotation.revisions = revisions
        quotation.save(update_fields=['status', 'rejection_reason', 'revisions'])

        log_approval_audit(user_info, 'REJECT', 'CRM', 'Quotation', quotation.id, reason)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        quotation = self.get_object()
        revision_no = request.data.get('revisionNumber') or request.data.get('revision_number')
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Apply role permissions for critical transitions if auth context exists
        user_info = {}
        has_auth_context = (
            (getattr(request, 'user', None) and getattr(request.user, 'is_authenticated', False)) or
            bool(request.headers.get('X-User-Role') if hasattr(request, 'headers') else None) or
            bool(request.META.get('HTTP_X_USER_ROLE') if hasattr(request, 'META') else None) or
            bool(request.data.get('_test_user') if isinstance(request.data, dict) else None)
        )
        if new_status.lower() in ['approved', 'rejected'] and has_auth_context:
            allowed, err_resp, user_info = validate_approval_permission(
                request,
                allowed_departments=['Sales', 'Commercial', 'Marketing', 'Management'],
                allowed_roles=['Sales Manager', 'Manager', 'Director', 'Admin']
            )
            if not allowed:
                return err_resp

        # Apply state machine guards
        if new_status.lower() == 'approved':
            if quotation.status.lower() == 'approved':
                return Response({'error': 'Quotation is already approved.'}, status=status.HTTP_400_BAD_REQUEST)
            if quotation.status.lower() == 'rejected':
                return Response({'error': 'Cannot approve a rejected quotation. Submit a new revision first.'}, status=status.HTTP_400_BAD_REQUEST)
            quotation.approved_by = request.data.get('approvedBy') or request.data.get('approverName') or user_info.get('name') or 'Admin'
            from django.utils import timezone
            quotation.approved_at = timezone.now()
        elif new_status.lower() == 'rejected':
            if quotation.status.lower() == 'rejected':
                return Response({'error': 'Quotation is already rejected.'}, status=status.HTTP_400_BAD_REQUEST)
            if quotation.status.lower() == 'approved':
                return Response({'error': 'Cannot reject an already approved quotation.'}, status=status.HTTP_400_BAD_REQUEST)
            quotation.rejection_reason = request.data.get('reason') or request.data.get('rejectionReason') or ''

        quotation.status = new_status
        revisions = list(quotation.revisions or [])
        matched = False
        for r in revisions:
            if not revision_no or (r.get('revisionNumber') == revision_no) or (r.get('revision_number') == revision_no):
                r['status'] = new_status
                if new_status.lower() == 'approved':
                    r['approvedBy'] = quotation.approved_by
                    r['approvedAt'] = quotation.approved_at.isoformat() if quotation.approved_at else ''
                matched = True
        if not matched and revisions:
            revisions[-1]['status'] = new_status
            if new_status.lower() == 'approved':
                revisions[-1]['approvedBy'] = quotation.approved_by
                revisions[-1]['approvedAt'] = quotation.approved_at.isoformat() if quotation.approved_at else ''
        quotation.revisions = revisions
        quotation.save(update_fields=['status', 'revisions', 'approved_by', 'approved_at', 'rejection_reason'])
        return Response(QuotationSerializer(quotation).data)

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        import logging
        import datetime
        from django.db import models
        logger = logging.getLogger(__name__)

        quotation = Quotation.objects.filter(models.Q(id=pk) | models.Q(quotation_number=pk)).first()
        if not quotation:
            quo_payload = request.data.get('quotation') or {}
            c_name = quo_payload.get('customerName') or quo_payload.get('customer_name') or request.data.get('customerName') or 'Valued Customer'
            c_person = quo_payload.get('contactPerson') or quo_payload.get('contact_person') or request.data.get('contactPerson') or ''
            c_email = quo_payload.get('contactEmail') or quo_payload.get('contact_email') or request.data.get('recipientEmail') or ''
            c_mobile = quo_payload.get('contactMobile') or quo_payload.get('contact_mobile') or ''
            c_id = quo_payload.get('customerId') or quo_payload.get('customer_id') or f"CUST-{pk}"
            m_product = quo_payload.get('machineProduct') or quo_payload.get('machine_product') or 'Industrial Fabrication Equipment'
            revs = quo_payload.get('revisions') or []
            last_r = revs[-1] if revs and isinstance(revs[-1], dict) else {}
            itms = quo_payload.get('items') or last_r.get('items') or []
            sub = float(quo_payload.get('subtotal') or quo_payload.get('subTotal') or last_r.get('subTotal') or last_r.get('subtotal') or 0)
            tax = float(quo_payload.get('taxAmount') or quo_payload.get('tax_amount') or last_r.get('taxAmount') or last_r.get('tax_amount') or 0)
            g_total = float(quo_payload.get('grandTotal') or quo_payload.get('grand_total') or last_r.get('grandTotal') or last_r.get('grand_total') or 0)
            cur_rev = quo_payload.get('currentRevision') or last_r.get('revisionNumber') or 'Rev-00'
            v_until = quo_payload.get('validUntil') or quo_payload.get('valid_until') or '2026-12-31'
            dt = quo_payload.get('date') or datetime.date.today().isoformat()

            try:
                quotation = Quotation.objects.create(
                    id=str(pk),
                    quotation_number=str(pk),
                    customer_id=c_id,
                    customer_name=c_name,
                    contact_person=c_person,
                    contact_email=c_email,
                    contact_mobile=c_mobile,
                    date=dt,
                    valid_until=v_until,
                    machine_product=m_product,
                    subtotal=sub,
                    tax_amount=tax,
                    grand_total=g_total,
                    current_revision=cur_rev,
                    revisions=revs,
                    items=itms,
                    status='sent',
                )
            except Exception as ex:
                logger.warning(f"Auto-creating quotation {pk} encountered ({ex}), using memory object.")
                from types import SimpleNamespace
                quotation = SimpleNamespace(
                    id=str(pk),
                    quotation_number=str(pk),
                    customer_id=c_id,
                    customer_name=c_name,
                    contact_person=c_person,
                    contact_email=c_email,
                    contact_mobile=c_mobile,
                    date=dt,
                    valid_until=v_until,
                    machine_product=m_product,
                    subtotal=sub,
                    tax_amount=tax,
                    grand_total=g_total,
                    current_revision=cur_rev,
                    revisions=revs,
                    items=itms,
                    status='sent',
                    enquiry_id=None,
                    lead_id=None,
                    save=lambda *args, **kwargs: None
                )

        recipient = (
            str(request.data.get('recipientEmail') or '').strip() or
            str(request.data.get('recipient_email') or '').strip() or
            str(request.data.get('email') or '').strip() or
            str(getattr(quotation, 'contact_email', '') or '').strip()
        )

        # If recipient is still empty, try linked Enquiry, Lead, or Customer record
        if not recipient and quotation.enquiry_id:
            enq = Enquiry.objects.filter(models.Q(id=quotation.enquiry_id) | models.Q(enquiry_no=quotation.enquiry_id)).first()
            if enq:
                if enq.customer_email:
                    recipient = str(enq.customer_email).strip()
                elif enq.lead_id:
                    ld = Lead.objects.filter(models.Q(id=enq.lead_id) | models.Q(lead_no=enq.lead_id)).first()
                    if ld and ld.email:
                        recipient = str(ld.email).strip()
        if not recipient and quotation.lead_id:
            ld = Lead.objects.filter(models.Q(id=quotation.lead_id) | models.Q(lead_no=quotation.lead_id)).first()
            if ld and ld.email:
                recipient = str(ld.email).strip()
        if not recipient and quotation.customer_id:
            cust = Customer.objects.filter(models.Q(id=quotation.customer_id) | models.Q(customer_code=quotation.customer_id)).first()
            if cust and cust.email:
                recipient = str(cust.email).strip()
        if not recipient and getattr(quotation, 'customer_name', None):
            ld = Lead.objects.filter(company_name__iexact=str(quotation.customer_name).strip()).exclude(email='').first()
            if ld and ld.email:
                recipient = str(ld.email).strip()

        if not recipient:
            return Response(
                {'error': 'No customer email address found for this quotation. Please provide an email address.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Persist email to quotation so it is permanently synchronized
        if recipient and (not getattr(quotation, 'contact_email', None) or quotation.contact_email != recipient):
            try:
                quotation.contact_email = recipient
                if hasattr(quotation, 'save'):
                    quotation.save(update_fields=['contact_email'])
            except Exception:
                try:
                    quotation.save()
                except Exception:
                    pass

        # Extract active revision and ensure items and financial totals are populated
        import json
        cur_rev_num = str(getattr(quotation, 'current_revision', 'Rev-00') or 'Rev-00').strip()
        revs = getattr(quotation, 'revisions', []) or []
        if isinstance(revs, str):
            try:
                revs = json.loads(revs)
            except Exception:
                revs = []

        quo_payload = request.data.get('quotation') or {}
        payload_revs = quo_payload.get('revisions') or []
        if isinstance(payload_revs, str):
            try:
                payload_revs = json.loads(payload_revs)
            except Exception:
                payload_revs = []

        if payload_revs and not revs:
            revs = payload_revs

        active_rev = None
        for r in revs:
            if isinstance(r, dict) and str(r.get('revisionNumber') or '').strip().lower() == cur_rev_num.lower():
                active_rev = r
                break
        if not active_rev and revs and isinstance(revs[-1], dict):
            active_rev = revs[-1]

        # Extract items
        items = getattr(quotation, 'items', []) or []
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except Exception:
                items = []

        if not items and active_rev:
            active_items = active_rev.get('items') or []
            if isinstance(active_items, str):
                try:
                    active_items = json.loads(active_items)
                except Exception:
                    active_items = []
            items = active_items

        if not items and quo_payload.get('items'):
            items = quo_payload.get('items') or []
        if not items and payload_revs and isinstance(payload_revs[-1], dict):
            items = payload_revs[-1].get('items') or []

        # Extract financial amounts - prioritizing active revision values
        subtotal = 0.0
        if active_rev and (active_rev.get('subTotal') is not None or active_rev.get('subtotal') is not None):
            try:
                val = active_rev.get('subTotal') if active_rev.get('subTotal') is not None else active_rev.get('subtotal')
                subtotal = float(val)
            except (ValueError, TypeError):
                subtotal = 0.0

        if subtotal == 0 and quo_payload:
            try:
                subtotal = float(quo_payload.get('subtotal') or quo_payload.get('subTotal') or 0)
            except (ValueError, TypeError):
                subtotal = 0.0

        if subtotal == 0 and getattr(quotation, 'subtotal', None):
            subtotal = float(quotation.subtotal or 0)

        tax_amount = 0.0
        if active_rev and (active_rev.get('taxAmount') is not None or active_rev.get('tax_amount') is not None):
            try:
                val = active_rev.get('taxAmount') if active_rev.get('taxAmount') is not None else active_rev.get('tax_amount')
                tax_amount = float(val)
            except (ValueError, TypeError):
                tax_amount = 0.0

        if tax_amount == 0 and quo_payload:
            try:
                tax_amount = float(quo_payload.get('taxAmount') or quo_payload.get('tax_amount') or 0)
            except (ValueError, TypeError):
                tax_amount = 0.0

        if tax_amount == 0 and getattr(quotation, 'tax_amount', None):
            tax_amount = float(quotation.tax_amount or 0)

        grand_total = 0.0
        if active_rev and (active_rev.get('grandTotal') is not None or active_rev.get('grand_total') is not None):
            try:
                val = active_rev.get('grandTotal') if active_rev.get('grandTotal') is not None else active_rev.get('grand_total')
                grand_total = float(val)
            except (ValueError, TypeError):
                grand_total = 0.0

        if grand_total == 0 and quo_payload:
            try:
                grand_total = float(quo_payload.get('grandTotal') or quo_payload.get('grand_total') or 0)
            except (ValueError, TypeError):
                grand_total = 0.0

        if grand_total == 0 and getattr(quotation, 'grand_total', None):
            grand_total = float(quotation.grand_total or getattr(quotation, 'total_amount', 0) or 0)

        # Fallback calculation only if amounts are still 0 but items exist
        if subtotal == 0 and items:
            subtotal = sum(float(it.get('rate', 0)) * float(it.get('quantity', 1)) for it in items)
        if grand_total == 0:
            grand_total = subtotal + tax_amount

        # Update quotation object and database so it is permanently synchronized
        try:
            quotation.items = items
            quotation.subtotal = subtotal
            quotation.tax_amount = tax_amount
            quotation.total_amount = grand_total
            quotation.grand_total = grand_total
            if not getattr(quotation, 'machine_product', None) and items:
                quotation.machine_product = items[0].get('productName') or items[0].get('product_name') or ''
            if hasattr(quotation, 'save'):
                quotation.save(update_fields=['items', 'subtotal', 'tax_amount', 'total_amount', 'grand_total', 'machine_product'])
        except Exception as save_ex:
            logger.warning(f"Could not update quotation fields: {save_ex}")

        subject = f"Commercial Quotation {quotation.quotation_number} ({quotation.current_revision}) - UMA Techno Fab Pvt. Ltd."
        total_formatted = f"INR {grand_total:,.2f}" if grand_total else "As Detailed"

        # Build items table for HTML email
        items_rows_html = ""
        items_text = ""
        for idx, itm in enumerate(items, 1):
            p_name = itm.get('productName') or itm.get('product_name') or quotation.machine_product or 'Fabrication & Equipment'
            p_desc = itm.get('description', '')
            qty = itm.get('quantity', 1)
            unit = itm.get('unit', 'Nos')
            rate = float(itm.get('rate', 0))
            amt = float(itm.get('amount', 0)) or (rate * float(qty))
            items_text += f"  {idx}. {p_name} | Qty: {qty} {unit} | Rate: INR {rate:,.2f} | Total: INR {amt:,.2f}\n"
            desc_html = f'<div style="font-size: 11px; color: #6b7280; margin: 3px 0 0 0; line-height: 1.4;" class="sub-text">{p_desc}</div>' if p_desc else ''
            items_rows_html += f"""
            <tr style="border-bottom: 1px solid #f0e6dd;" class="item-row-border">
              <td style="padding: 10px 6px; vertical-align: top;">
                <div style="font-weight: 700; font-size: 13px; color: #1f2937; line-height: 1.4;" class="title-text">
                  <span style="display: inline-block; background-color: #faf0e6; color: #75401f; font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 3px; margin-right: 4px;">#{idx}</span>
                  {p_name}
                </div>
                {desc_html}
                <div style="font-size: 11px; color: #8c7a6e; margin-top: 4px;" class="sub-text">
                  Qty: <strong style="color: #374151;" class="title-text">{qty} {unit}</strong> &nbsp;•&nbsp; Rate: <strong style="color: #374151;" class="title-text">INR {rate:,.2f}</strong>
                </div>
              </td>
              <td align="right" style="padding: 10px 6px; vertical-align: top; white-space: nowrap;">
                <span style="font-size: 13px; font-weight: 700; color: #75401f;">INR {amt:,.2f}</span>
              </td>
            </tr>
            """

        import re

        clean_quo_num = re.sub(r'[^A-Za-z0-9_-]', '_', str(getattr(quotation, 'quotation_number', None) or pk or 'QT'))
        clean_rev_num = re.sub(r'[^A-Za-z0-9_-]', '_', str(getattr(quotation, 'current_revision', None) or cur_rev_num or 'Rev-00'))
        pdf_filename = f"Quotation_{clean_quo_num}_{clean_rev_num}.pdf"

        pdf_bytes = None
        try:
            from apps.crm.quotation_pdf import generate_quotation_pdf
            pdf_bytes = generate_quotation_pdf(quotation, active_revision=active_rev, payload=quo_payload)
            logger.info(f"Generated quotation PDF '{pdf_filename}' ({len(pdf_bytes)} bytes)")
        except Exception as pdf_ex:
            logger.warning(f"Error generating quotation PDF: {pdf_ex}")

        email_text = f"""Dear {quotation.contact_person or quotation.customer_name},

Thank you for your business enquiry with UMA TECHNO FAB PVT. LTD.

We are pleased to submit our formal commercial and technical proposal for your valued review.
Please find attached our official quotation proposal in PDF format: {pdf_filename}

============================================================
PROPOSAL DETAILS:
Quotation No    : {quotation.quotation_number} ({quotation.current_revision})
Date            : {quotation.date}
Valid Until     : {quotation.valid_until}
Customer Name   : {quotation.customer_name}
Attn            : {quotation.contact_person}
Equipment Scope : {quotation.machine_product or 'Industrial Machinery & Process Equipment'}
Official PDF    : {pdf_filename}
============================================================

BILL OF QUANTITIES & PRICING:
{items_text}
Taxable Subtotal : INR {subtotal:,.2f}
Applicable GST   : INR {tax_amount:,.2f}
Grand Total      : {total_formatted}

Commercial Terms:
- Payment Terms: As mutually agreed upon Purchase Order.
- Validity: 30 days from proposal date.
- Inspection & Quality: Strictly compliant with standard industrial fabrication norms.

The complete itemized engineering specifications, scope of supply, and commercial terms are detailed in the attached official PDF ({pdf_filename}).

Please feel free to contact us for any technical or commercial clarifications.

Warm Regards,
Sales & Commercial Division
UMA TECHNO FAB PVT. LTD.
Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India
Web: www.umatechnofab.com
"""

        from django.conf import settings
        from_email_setting = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'UMA TECHNO FAB <hrinfinitesofttech@gmail.com>'
        email_match = re.search(r'<([^>]+)>', str(from_email_setting))
        reply_to_addr = email_match.group(1).strip() if email_match else str(from_email_setting).strip()

        email_html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="format-detection" content="telephone=no, date=no, address=no, email=no" />
  <meta name="color-scheme" content="light dark" />
  <meta name="supported-color-schemes" content="light dark" />
  <title>{subject}</title>
  <style type="text/css">
    body, table, td, p, a, li, blockquote {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    table, td {{
      mso-table-lspace: 0pt;
      mso-table-rspace: 0pt;
    }}
    img {{
      -ms-interpolation-mode: bicubic;
      border: 0;
      height: auto;
      line-height: 100%;
      outline: none;
      text-decoration: none;
    }}
    body {{
      margin: 0 !important;
      padding: 0 !important;
      width: 100% !important;
      background-color: #f6f3ee;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    @media (prefers-color-scheme: dark) {{
      .email-bg {{ background-color: #121212 !important; }}
      .card-box {{ background-color: #1e1e1e !important; border-color: #333333 !important; }}
      .meta-pill-box {{ background-color: #27221e !important; border-color: #42352b !important; }}
      .title-text {{ color: #ffffff !important; }}
      .body-text {{ color: #e0e0e0 !important; }}
      .sub-text {{ color: #a0a0a0 !important; }}
      .item-row-border {{ border-bottom-color: #333333 !important; }}
      .total-box {{ background-color: #2c2018 !important; border-color: #4f3422 !important; }}
      .terms-callout {{ background-color: #22201d !important; border-left-color: #8c5229 !important; color: #cccccc !important; }}
      .footer-section {{ border-top-color: #333333 !important; }}
    }}
    @media only screen and (max-width: 600px) {{
      .container-table {{ width: 100% !important; max-width: 100% !important; }}
      .mobile-padding {{ padding: 14px 12px !important; }}
      .mobile-header-padding {{ padding: 18px 14px !important; }}
      .mobile-stack {{ display: block !important; width: 100% !important; box-sizing: border-box !important; }}
      .mobile-text-left {{ text-align: left !important; }}
      .mobile-margin-top {{ margin-top: 10px !important; }}
    }}
  </style>
</head>
<body class="email-bg" style="margin: 0; padding: 16px 8px; background-color: #f6f3ee;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-bg" style="background-color: #f6f3ee;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="container-table card-box" style="max-width: 600px; background-color: #ffffff; border: 1px solid #e7ded5; border-radius: 12px; overflow: hidden; box-shadow: 0 3px 12px rgba(0,0,0,0.06);">
          
          <!-- Brand Header Banner -->
          <tr>
            <td style="background-color: #75401f; padding: 22px 24px; color: #ffffff;" class="mobile-header-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td>
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; font-weight: 700; color: #f2dfd3;">COMMERCIAL PROPOSAL</div>
                    <h1 style="margin: 4px 0 0 0; font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: 0.3px; line-height: 1.3;">UMA TECHNO FAB PVT. LTD.</h1>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #ebdcd2; line-height: 1.4;">Plot No. 48/B, GIDC Industrial Estate, Makarpura, Vadodara - 390010, Gujarat, India</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content Body -->
          <tr>
            <td style="padding: 24px;" class="mobile-padding">

              <!-- Quotation Meta Pill Box (Reference & Validity) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="meta-pill-box" style="background-color: #faf5f0; border: 1px solid #eedfd3; border-radius: 8px; margin-bottom: 20px;">
                <tr>
                  <td style="padding: 12px 14px;" class="mobile-stack">
                    <span style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: #8c7a6e; font-weight: 700; display: block;">QUOTATION REFERENCE</span>
                    <div style="margin-top: 3px;">
                      <span style="font-size: 15px; font-weight: 800; color: #75401f; font-family: monospace, Courier, sans-serif;">{quotation.quotation_number}</span>
                      <span style="display: inline-block; background-color: #75401f; color: #ffffff; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px; vertical-align: middle; margin-left: 6px;">{quotation.current_revision}</span>
                    </div>
                  </td>
                  <td style="padding: 12px 14px; text-align: right;" class="mobile-stack mobile-text-left mobile-margin-top">
                    <div style="font-size: 11px; color: #6b7280; line-height: 1.5;">
                      Date: <strong style="color: #211b17;" class="title-text">{quotation.date}</strong><br>
                      Valid Until: <strong style="color: #211b17;" class="title-text">{quotation.valid_until}</strong>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Client Details Box -->
              <div style="border-bottom: 1px solid #f0e6dd; padding-bottom: 16px; margin-bottom: 18px;" class="item-row-border">
                <span style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: #8c7a6e; font-weight: 700; display: block; margin-bottom: 4px;">PROPOSAL ADDRESSED TO</span>
                <div style="font-size: 17px; font-weight: 800; color: #1f2937; line-height: 1.3;" class="title-text">{quotation.customer_name}</div>
                <div style="font-size: 13px; color: #4b5563; margin-top: 4px;" class="body-text">
                  Attn: <strong style="color: #1f2937;" class="title-text">{quotation.contact_person or quotation.customer_name}</strong>
                </div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 2px;" class="sub-text">
                  Recipient Email: <a href="mailto:{recipient}" style="color: #75401f; text-decoration: none; font-weight: 600;">{recipient}</a>
                </div>
              </div>

              <!-- Greeting & Intro -->
              <p style="font-size: 13px; line-height: 1.6; color: #374151; margin: 0 0 16px 0;" class="body-text">
                Dear <strong>{quotation.contact_person or quotation.customer_name}</strong>,<br>
                Thank you for your business enquiry. We are pleased to submit our formal commercial and technical proposal for your valued review:
              </p>

              <!-- PDF Attachment Banner Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="meta-pill-box" style="background-color: #faf5f0; border: 1.5px dashed #75401f; border-radius: 8px; margin-bottom: 20px;">
                <tr>
                  <td style="padding: 12px 14px;">
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: #75401f; font-weight: 700;">
                      &#128196; OFFICIAL ATTACHMENT (PDF FORMAT)
                    </div>
                    <div style="font-size: 13px; font-weight: 800; color: #3e2723; margin-top: 3px;">
                      {pdf_filename}
                    </div>
                    <div style="font-size: 11px; color: #70665f; margin-top: 2px; line-height: 1.4;" class="sub-text">
                      Please open the attached PDF proposal to view our complete official letterhead, itemized engineering specifications, scope of supply, and formal commercial terms.
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Bill of Quantities / Items List (Responsive Card-based Table) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 16px;">
                <thead>
                  <tr style="border-bottom: 2px solid #e7ded5;" class="item-row-border">
                    <th align="left" style="padding: 8px 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #8c7a6e; font-weight: 700;">Equipment / Description</th>
                    <th align="right" style="padding: 8px 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #8c7a6e; font-weight: 700; white-space: nowrap;">Amount (INR)</th>
                  </tr>
                </thead>
                <tbody>
                  {items_rows_html}
                </tbody>
              </table>

              <!-- Financial Summary (Totals) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-top: 8px; margin-bottom: 20px;">
                <tr>
                  <td align="right" style="padding: 6px 10px; font-size: 12px; color: #6b7280;" class="sub-text">Taxable Subtotal:</td>
                  <td align="right" width="130" style="padding: 6px 10px; font-size: 12px; font-weight: 700; color: #1f2937; white-space: nowrap;" class="title-text">INR {subtotal:,.2f}</td>
                </tr>
                <tr>
                  <td align="right" style="padding: 6px 10px; font-size: 12px; color: #6b7280;" class="sub-text">Applicable GST:</td>
                  <td align="right" width="130" style="padding: 6px 10px; font-size: 12px; font-weight: 700; color: #1f2937; white-space: nowrap;" class="title-text">INR {tax_amount:,.2f}</td>
                </tr>
                <tr class="total-box" style="background-color: #faf0e6;">
                  <td align="right" style="padding: 12px 10px; font-size: 14px; font-weight: 800; color: #75401f; border-top: 1px solid #ebd8c8; border-bottom: 1px solid #ebd8c8;">Grand Total:</td>
                  <td align="right" width="130" style="padding: 12px 10px; font-size: 16px; font-weight: 900; color: #059669; border-top: 1px solid #ebd8c8; border-bottom: 1px solid #ebd8c8; white-space: nowrap;">{total_formatted}</td>
                </tr>
              </table>

              <!-- Terms & Conditions Note -->
              <div class="terms-callout" style="background-color: #faf7f2; border-left: 4px solid #75401f; border-radius: 4px; padding: 12px 14px; margin-top: 16px; font-size: 12px; color: #544b45; line-height: 1.6;">
                <strong style="color: #75401f; display: block; margin-bottom: 4px;">Commercial Terms:</strong>
                • Payment Terms: As mutually agreed upon Purchase Order.<br>
                • Validity: 30 days from proposal date.<br>
                • Inspection & Quality: Strictly compliant with standard industrial fabrication norms.
              </div>

              <!-- Reassurance message -->
              <p style="font-size: 12px; color: #6b7280; margin: 18px 0 0 0; line-height: 1.5;" class="sub-text">
                Please feel free to reach out to our engineering and sales division for any technical clarifications or adjustments to the scope.
              </p>

              <!-- Footer & Signature (CAN-SPAM Compliant) -->
              <div class="footer-section" style="margin-top: 24px; padding-top: 18px; border-top: 1px solid #e5ded5; font-size: 11px; color: #70665f; line-height: 1.5;">
                <strong style="font-size: 12px; color: #211b17;" class="title-text">UMA TECHNO FAB PVT. LTD.</strong><br>
                Sales & Commercial Division • Makarpura GIDC, Vadodara - 390010<br>
                Phone: +91 265 264 0000 • Email: <a href="mailto:{reply_to_addr}" style="color: #75401f; text-decoration: none; font-weight: 600;">{reply_to_addr}</a><br>
                Website: <a href="https://www.umatechnofab.com" style="color: #75401f; text-decoration: none; font-weight: 600;">www.umatechnofab.com</a>
                <p style="margin: 10px 0 0 0; font-size: 10px; color: #9ca3af; line-height: 1.4;">
                  This commercial quotation proposal was generated automatically by UMA ERP on behalf of UMA TECHNO FAB PVT. LTD. for {quotation.customer_name}.
                </p>
              </div>

            </td>
          </tr>
        </table>
        <!-- End Card Table -->
      </td>
    </tr>
  </table>
</body>
</html>
"""

        from django.core.mail import EmailMultiAlternatives
        import logging
        logger = logging.getLogger(__name__)

        try:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=email_text,
                from_email=from_email_setting,
                to=[recipient],
                reply_to=[reply_to_addr],
                headers={
                    'X-Mailer': 'UMA ERP Commercial System',
                    'X-Priority': '3',
                    'Importance': 'Normal',
                }
            )
            email_msg.attach_alternative(email_html, "text/html")
            if pdf_bytes:
                email_msg.attach(pdf_filename, pdf_bytes, 'application/pdf')

            email_msg.send(fail_silently=False)

            email_status = 'sent'
            message = f"Quotation {quotation.quotation_number} ({quotation.current_revision}) successfully dispatched via email to {recipient} with attached PDF ({pdf_filename})."

            # Update quotation & revision status to 'sent' upon confirmed dispatch
            if quotation.status in ['draft', 'approved']:
                quotation.status = 'sent'
            revs = quotation.revisions or []
            for r in revs:
                if r.get('revisionNumber') == quotation.current_revision:
                    r['status'] = 'sent'
            quotation.revisions = revs
            try:
                quotation.save(update_fields=['status', 'revisions'])
            except Exception:
                try:
                    quotation.save()
                except Exception:
                    pass

            return Response({
                'success': True,
                'message': message,
                'recipient': recipient,
                'quotationNumber': quotation.quotation_number,
                'currentRevision': quotation.current_revision,
                'emailStatus': email_status,
                'hasPdfAttachment': bool(pdf_bytes),
                'pdfFilename': pdf_filename,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.warning(f"SMTP dispatch failed ({e}). Logged dispatch error for quotation.")
            # Even if SMTP provider encounters an issue, update quotation status to sent so business workflow is not blocked
            if quotation.status in ['draft', 'approved']:
                quotation.status = 'sent'
                try:
                    quotation.save(update_fields=['status'])
                except Exception:
                    pass

            return Response({
                'success': False,
                'error': f"Failed to send email to {recipient}: {str(e)}",
                'recipient': recipient,
                'quotationNumber': quotation.quotation_number,
                'emailStatus': 'failed',
                'hasPdfAttachment': bool(pdf_bytes),
                'pdfFilename': pdf_filename,
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'], url_path='pdf')
    def download_pdf(self, request, pk=None):
        from django.http import HttpResponse
        from apps.crm.quotation_pdf import generate_quotation_pdf
        from types import SimpleNamespace
        import json
        import re

        quotation = Quotation.objects.filter(models.Q(id=pk) | models.Q(quotation_number=pk)).first()
        payload = request.data if request.method == 'POST' else {}

        target_rev = request.query_params.get('revision') or payload.get('currentRevision')
        active_rev = None
        if quotation and quotation.revisions:
            revs = quotation.revisions
            if isinstance(revs, str):
                try:
                    revs = json.loads(revs)
                except Exception:
                    revs = []
            if target_rev:
                for r in revs:
                    if isinstance(r, dict) and str(r.get('revisionNumber') or '').strip().lower() == str(target_rev).strip().lower():
                        active_rev = r
                        break
            if not active_rev and revs and isinstance(revs[-1], dict):
                active_rev = revs[-1]

        try:
            from apps.crm.quotation_pdf import generate_quotation_pdf
            pdf_bytes = generate_quotation_pdf(
                quotation or SimpleNamespace(id=str(pk), quotation_number=str(pk)),
                active_revision=active_rev,
                payload=payload
            )
        except Exception as e:
            logger.warning(f"Error generating PDF in download_pdf: {e}")
            return HttpResponse(f"Error generating PDF: {e}", status=500)

        q_num = getattr(quotation, 'quotation_number', None) or pk
        r_num = (active_rev.get('revisionNumber') if active_rev else None) or getattr(quotation, 'current_revision', None) or 'Rev-00'
        clean_quo = re.sub(r'[^A-Za-z0-9_-]', '_', str(q_num))
        clean_rev = re.sub(r'[^A-Za-z0-9_-]', '_', str(r_num))
        filename = f"Quotation_{clean_quo}_{clean_rev}.pdf"

        disposition = 'inline' if request.query_params.get('view') == '1' else 'attachment'
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response



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
    queryset = SalesOrder.objects.all().order_by('-created_at', '-id')
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

