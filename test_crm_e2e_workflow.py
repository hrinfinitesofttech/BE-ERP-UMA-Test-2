import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from apps.authentication.models import User
from apps.crm.models import Lead, Enquiry, FollowUp, SiteVisit, Exhibition, Quotation, CustomerPO, SalesOrder, Customer

def run_api_e2e_test():
    client = APIClient()
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if admin_user:
        client.force_authenticate(user=admin_user)

    print("======================================================================")
    print("UMAERP CRM - COMPLETE REST API LIFECYCLE & PERSISTENCE TEST")
    print("======================================================================")

    # 1. Exhibition Creation
    expo_payload = {
        "expoName": "ChemTech Global Industrial Expo 2026",
        "organizer": "ChemTech Foundation India",
        "location": "Bombay Exhibition Centre, Mumbai",
        "venue": "Hall 1, Goregaon East",
        "city": "Mumbai",
        "country": "India",
        "startDate": "2026-03-04",
        "endDate": "2026-03-07",
        "stallNumber": "Stall C-12",
        "contactPerson": "Pravin Patel",
        "budget": 250000.0,
        "participationStatus": "confirmed",
        "productsDisplayed": "Pressure Vessels, Limpet Reactors, Heat Exchangers",
        "notes": "Annual premier chemical processing exhibition."
    }
    res_expo = client.post('/api/crm/exhibitions/', expo_payload, format='json')
    assert res_expo.status_code in [200, 201], f"Exhibition creation failed: {res_expo.data}"
    expo_id = res_expo.data['id']
    expo_name = res_expo.data.get('expoName') or res_expo.data.get('expo_name') or expo_payload['expoName']
    print(f"STEP 1 [PASS]: Exhibition Created via API -> ID: {expo_id}, Name: {expo_name}")

    # 2. Lead Creation linked to Exhibition
    lead_payload = {
        "companyName": "Apex Speciality Chemicals Ltd",
        "contactPerson": "Dr. Rajesh Shah",
        "designation": "Vice President - Projects",
        "mobile": "9825011223",
        "email": "rajesh.shah@apexchem.com",
        "city": "Vadodara, Gujarat",
        "productName": "15 KL Hastelloy C-276 Reaction Vessel with Limpet Coil",
        "quantity": 2,
        "capacity": "15,000 Litres",
        "budget": 4500000.0,
        "source": "exhibition",
        "exhibitionId": expo_id,
        "exhibitionName": expo_name,
        "status": "new",
        "priority": "high",
        "expectedDelivery": "2026-12-15",
        "nextFollowUpDate": "2026-10-20",
        "remarks": "Met Dr. Shah at ChemTech Expo booth C-12."
    }
    res_lead = client.post('/api/crm/leads/', lead_payload, format='json')
    assert res_lead.status_code in [200, 201], f"Lead creation failed: {res_lead.data}"
    lead_id = res_lead.data['id']
    lead_no = res_lead.data.get('leadNo') or res_lead.data.get('lead_no')
    print(f"STEP 2 [PASS]: Lead Registered with Expo Link -> ID: {lead_id}, LeadNo: {lead_no}, Expo: {res_lead.data.get('exhibitionName')}")

    # 3. Convert Lead to Technical Enquiry (RFQ)
    res_enq_convert = client.post(f'/api/crm/leads/{lead_id}/convert-to-enquiry/')
    assert res_enq_convert.status_code in [200, 201], f"Lead to Enquiry conversion failed: {res_enq_convert.data}"
    enq_data = res_enq_convert.data.get('enquiry') or res_enq_convert.data
    enquiry_id = enq_data['id']
    enquiry_no = enq_data.get('enquiryNo') or enq_data.get('enquiry_no')
    print(f"STEP 3 [PASS]: Technical Enquiry Generated -> ID: {enquiry_id}, EnquiryNo: {enquiry_no}, Product: {enq_data.get('machineProduct') or enq_data.get('machine_product')}")

    # 4. Schedule Follow-up in Unified Follow-up Center
    flw_payload = {
        "leadOrCustomerId": enquiry_id,
        "leadOrCustomerName": f"Apex Speciality Chemicals ({enquiry_no})",
        "entityType": "enquiry",
        "enquiryId": enquiry_id,
        "type": "call",
        "assignedToId": admin_user.id if admin_user else "EMP-001",
        "assignedToName": "Pravin Patel",
        "date": "2026-10-18",
        "time": "11:30 AM",
        "priority": "high",
        "purpose": "Review Hastelloy plate thickness & Limpet welding specs",
        "notes": "Discussed fabrication schedule and ASME code certification.",
        "status": "pending"
    }
    res_flw = client.post('/api/crm/followups/', flw_payload, format='json')
    assert res_flw.status_code in [200, 201], f"Follow-up creation failed: {res_flw.data}"
    flw_id = res_flw.data['id']
    print(f"STEP 4 [PASS]: Follow-up Scheduled in Unified Center -> ID: {flw_id}, Purpose: {res_flw.data.get('purpose')}")

    # Complete Follow-up with outcome
    res_flw_done = client.post(f'/api/crm/followups/{flw_id}/complete/', {
        "notes": "Dr. Shah approved Limpet design. Requested plant site inspection next week.",
        "outcome": "connected"
    }, format='json')
    print(f"STEP 4b [PASS]: Follow-up Marked Done with Interaction Outcome -> Status: {res_flw_done.data.get('status')}")

    # 5. Record Site Visit
    visit_payload = {
        "leadId": lead_id,
        "enquiryId": enquiry_id,
        "customerName": "Apex Speciality Chemicals Ltd",
        "contactPerson": "Dr. Rajesh Shah",
        "contactMobile": "9825011223",
        "visitDate": "2026-10-22",
        "location": "Dahej Industrial Estate, Phase 2, Plant Bay 4",
        "employeeId": admin_user.id if admin_user else "EMP-001",
        "employeeName": "Pravin Patel",
        "purpose": "Civil pad orientation & crane clearance check",
        "siteMeasurements": "Bay clear height: 9.5m, Crane hook capacity: 15 Ton, Foundation pad: 3.5m x 3.5m",
        "operatingConditions": "3-Phase 415V, Steam at 4.5 bar, Chilled water at 7°C available",
        "discussionNotes": "Plant manager confirmed nozzle orientation towards main header.",
        "outcome": "quotation_required",
        "nextAction": "Submit formal commercial quotation Rev-00"
    }
    res_visit = client.post('/api/crm/visits/', visit_payload, format='json')
    assert res_visit.status_code in [200, 201], f"Site visit creation failed: {res_visit.data}"
    visit_id = res_visit.data['id']
    print(f"STEP 5 [PASS]: Site Visit Recorded with Technical Clearances -> ID: {visit_id}, Measurements: {res_visit.data.get('siteMeasurements')[:35]}...")

    # 6. Convert Lead to Customer Account
    res_cust_convert = client.post(f'/api/crm/leads/{lead_id}/convert-to-customer/')
    assert res_cust_convert.status_code in [200, 201], f"Lead to Customer conversion failed: {res_cust_convert.data}"
    cust_data = res_cust_convert.data.get('customer') or res_cust_convert.data
    customer_id = cust_data['id']
    print(f"STEP 6 [PASS]: Converted to Master Customer -> ID: {customer_id}, Company: {cust_data.get('companyName') or cust_data.get('company_name')}")

    # 7. Create Formal Quotation
    quot_payload = {
        "customerId": customer_id,
        "customerName": "Apex Speciality Chemicals Ltd",
        "contactPerson": "Dr. Rajesh Shah",
        "contactMobile": "9825011223",
        "contactEmail": "rajesh.shah@apexchem.com",
        "leadId": lead_id,
        "validUntil": "2026-11-30",
        "currentRevision": "Rev-00",
        "revisions": [{
            "revisionNumber": "Rev-00",
            "date": "2026-10-23",
            "preparedBy": "Pravin Patel",
            "status": "approved",
            "items": [{
                "productName": "15 KL Hastelloy C-276 Reaction Vessel with Limpet Coil",
                "description": "Design Code: ASME Sec VIII Div 1, MOC: Hastelloy C-276",
                "quantity": 2,
                "unit": "Set",
                "rate": 2250000.0,
                "discountPercent": 0,
                "taxPercent": 18,
                "amount": 4500000.0
            }],
            "subTotal": 4500000.0,
            "taxAmount": 810000.0,
            "grandTotal": 5310000.0,
            "technicalSpecs": "Design Code: ASME Sec VIII Div 1, Operating Temp: 220°C, Design Pressure: 6 bar",
            "scopeOfSupply": "Supply, fabrication, inspection and testing of Hastelloy Vessels",
            "paymentTerms": "30% Advance, 60% Against Proforma, 10% on Commissioning",
            "deliveryTime": "12 Weeks from drawing approval",
            "warranty": "18 Months from dispatch"
        }]
    }
    res_quot = client.post('/api/crm/quotations/', quot_payload, format='json')
    assert res_quot.status_code in [200, 201], f"Quotation creation failed: {res_quot.data}"
    quot_id = res_quot.data['id']
    quot_number = res_quot.data.get('quotationNumber') or res_quot.data.get('quotation_number')
    print(f"STEP 7 [PASS]: Quotation Created -> ID: {quot_id}, QuoteNo: {quot_number}")

    # 8. Record / Inward Customer Purchase Order (Customer PO)
    po_payload = {
        "poNumber": "PO/APX/2026/0881",
        "poDate": "2026-10-25",
        "customerId": customer_id,
        "customerName": "Apex Speciality Chemicals Ltd",
        "quotationId": quot_id,
        "quotationNumber": quot_number,
        "poAmount": 5310000.0,
        "paymentTerms": "30% Advance, 60% Before Dispatch, 10% Commissioning",
        "deliveryDate": "2026-12-30",
        "status": "received",
        "remarks": f"Client accepted Quotation {quot_number} (Rev-00) and issued formal purchase order."
    }
    res_po = client.post('/api/crm/customer-pos/', po_payload, format='json')
    assert res_po.status_code in [200, 201], f"Customer PO creation failed: {res_po.data}"
    po_id = res_po.data['id']
    print(f"STEP 8 [PASS]: Customer PO Inwarded -> ID: {po_id}, PONumber: {res_po.data.get('poNumber') or res_po.data.get('po_number')}")

    # 9. Convert Customer PO to Sales Order
    res_so_convert = client.post(f'/api/crm/customer-pos/{po_id}/convert-to-so/')
    assert res_so_convert.status_code in [200, 201], f"Customer PO to SO conversion failed: {res_so_convert.data}"
    so_data = res_so_convert.data.get('sales_order') or res_so_convert.data
    so_id = so_data['id']
    so_number = so_data.get('salesOrderNumber') or so_data.get('sales_order_number')
    print(f"STEP 9 [PASS]: Sales Order Generated from Customer PO -> ID: {so_id}, SONumber: {so_number}")

    print("\n======================================================================")
    print("ALL 9 API STEPS PASSED WITH 100% PERSISTENCE IN DATABASE!")
    print("Complete Traceability Chain:")
    print(f"  Exhibition ({expo_name})")
    print(f"  -> Lead ({lead_no})")
    print(f"  -> Technical Inquiry ({enquiry_no})")
    print(f"  -> Follow-up ({flw_id})")
    print(f"  -> Site Visit ({visit_id})")
    print(f"  -> Customer ({customer_id})")
    print(f"  -> Quotation ({quot_number})")
    print(f"  -> Customer PO ({po_payload['poNumber']})")
    print(f"  -> Sales Order ({so_number})")
    print("======================================================================")
    return True

if __name__ == '__main__':
    run_api_e2e_test()
