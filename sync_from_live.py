import urllib.request
import json
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from apps.crm.models import Lead, Customer, Contact, Enquiry, Opportunity, Quotation, CustomerPO, SalesOrder

LIVE_API_BASE = 'https://umaERP.pythonanywhere.com/api'

def sync_leads():
    print("[1] Syncing Leads from Live PythonAnywhere to Local Database...")
    url = f"{LIVE_API_BASE}/leads/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        count = 0
        for item in data:
            lead_id = item.get('id') or item.get('lead_no') or item.get('leadNo')
            if not lead_id:
                continue
            defaults = {
                'lead_no': item.get('lead_no') or item.get('leadNo') or lead_id,
                'company_name': item.get('company_name') or item.get('companyName') or 'Prospect Co',
                'industry': item.get('industry') or '',
                'website': item.get('website') or '',
                'gstin': item.get('gstin') or '',
                'address': item.get('address') or '',
                'city': item.get('city') or '',
                'state': item.get('state') or '',
                'country': item.get('country') or 'India',
                'pincode': str(item.get('pincode') or ''),
                'contact_person': item.get('contact_person') or item.get('contactPerson') or 'Contact Person',
                'designation': item.get('designation') or '',
                'mobile': str(item.get('mobile') or ''),
                'alt_mobile': str(item.get('alt_mobile') or item.get('altMobile') or ''),
                'email': item.get('email') or '',
                'whatsapp': str(item.get('whatsapp') or ''),
                'product_name': item.get('product_name') or item.get('productName') or 'Equipment',
                'machine_type': item.get('machine_type') or item.get('machineType') or '',
                'quantity': int(item.get('quantity') or 1),
                'capacity': str(item.get('capacity') or ''),
                'application': item.get('application') or '',
                'requirement_description': item.get('requirement_description') or item.get('requirementDescription') or '',
                'expected_delivery': str(item.get('expected_delivery') or item.get('expectedDelivery') or ''),
                'budget': float(item.get('budget') or 0),
                'priority': item.get('priority') or 'medium',
                'source': item.get('source') or 'website',
                'assigned_sales_person_id': item.get('assigned_sales_person_id') or item.get('assignedSalesPersonId') or '',
                'assigned_sales_person_name': item.get('assigned_sales_person_name') or item.get('assignedSalesPersonName') or '',
                'status': item.get('status') or 'new',
                'next_follow_up_date': str(item.get('next_follow_up_date') or item.get('nextFollowUpDate') or ''),
                'remarks': item.get('remarks') or '',
                'created_date': str(item.get('created_date') or item.get('createdDate') or ''),
                'converted_customer_id': item.get('converted_customer_id') or item.get('convertedCustomerId') or None,
                'converted_enquiry_id': item.get('converted_enquiry_id') or item.get('convertedEnquiryId') or None,
                'converted_opportunity_id': item.get('converted_opportunity_id') or item.get('convertedOpportunityId') or None,
                'attachments': item.get('attachments') or [],
            }
            Lead.objects.update_or_create(id=lead_id, defaults=defaults)
            count += 1
        print(f"  -> Leads Synced: {count} (Total in Local DB: {Lead.objects.count()})")
    except Exception as e:
        print(f"  -> Failed to sync leads: {e}")

if __name__ == '__main__':
    sync_leads()
