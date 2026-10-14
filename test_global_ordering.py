import os
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from apps.crm.models import Lead, Customer
from apps.store.models import ItemMaster, ItemCategory, UOMMaster
from apps.organization.models import Department, Role
from apps.accounting.models import BankAccount, ExpenseEntry

client = APIClient()

def test_module_ordering(name, list_url, create_url, create_payload, id_key='id'):
    print(f"\n--- Testing {name} ---")
    
    # 1. Create first record
    res1 = client.post(create_url, create_payload[0], format='json')
    assert res1.status_code in [200, 201], f"Failed to create record 1: {res1.status_code} {res1.data}"
    rec1_id = res1.data.get(id_key) or res1.data.get('id')
    print(f"Created Record 1: {rec1_id}")

    # Small pause to guarantee distinct timestamp if backend timestamp is used
    time.sleep(0.05)

    # Verify record 1 is at index 0
    list_res1 = client.get(list_url)
    assert list_res1.status_code == 200, f"Failed to get list: {list_res1.status_code}"
    results1 = list_res1.data.get('results', list_res1.data) if isinstance(list_res1.data, dict) else list_res1.data
    first_row1 = results1[0].get(id_key) or results1[0].get('id')
    print(f"Current Row 1: {first_row1} (Expected: {rec1_id})")
    assert first_row1 == rec1_id, f"Record 1 is NOT at Row 1! Found: {first_row1}"

    # 2. Create second record consecutively
    res2 = client.post(create_url, create_payload[1], format='json')
    assert res2.status_code in [200, 201], f"Failed to create record 2: {res2.status_code} {res2.data}"
    rec2_id = res2.data.get(id_key) or res2.data.get('id')
    print(f"Created Record 2: {rec2_id}")

    # Verify record 2 is now at index 0 (Row 1), and record 1 is at index 1 (Row 2)
    list_res2 = client.get(list_url)
    assert list_res2.status_code == 200, f"Failed to get list: {list_res2.status_code}"
    results2 = list_res2.data.get('results', list_res2.data) if isinstance(list_res2.data, dict) else list_res2.data
    first_row2 = results2[0].get(id_key) or results2[0].get('id')
    second_row2 = results2[1].get(id_key) or results2[1].get('id')
    print(f"Current Row 1: {first_row2} (Expected: {rec2_id})")
    print(f"Current Row 2: {second_row2} (Expected: {rec1_id})")
    assert first_row2 == rec2_id, f"Record 2 is NOT at Row 1! Found: {first_row2}"
    assert second_row2 == rec1_id, f"Record 1 is NOT at Row 2! Found: {second_row2}"
    print(f"PASS: {name} newest record appears at Row No. 1!")
    return [rec1_id, rec2_id]


if __name__ == '__main__':
    created_leads = []
    created_items = []
    created_banks = []

    ts = int(time.time())

    try:
        # Pre-clean any previous items
        ItemMaster.objects.filter(item_code__startswith="TEST-ITM-").delete()

        # Test CRM Leads
        leads = test_module_ordering(
            name="CRM Leads",
            list_url="/api/leads/",
            create_url="/api/leads/",
            create_payload=[
                {
                    "company_name": f"Test Alpha Corp {ts}",
                    "contact_person": "Alpha Contact",
                    "phone": "+919876543210",
                    "email": "alpha@example.com",
                    "source": "Website",
                    "product_name": "Pharma Autoclave"
                },
                {
                    "company_name": f"Test Beta Corp {ts}",
                    "contact_person": "Beta Contact",
                    "phone": "+919876543211",
                    "email": "beta@example.com",
                    "source": "Exhibition",
                    "product_name": "Cleanroom Door"
                }
            ],
            id_key="lead_no"
        )
        created_leads.extend(leads)

        # Test Store Item Master
        items = test_module_ordering(
            name="Store Items",
            list_url="/api/items/",
            create_url="/api/items/",
            create_payload=[
                {
                    "item_code": f"TEST-ITM-{ts}-1",
                    "item_name": "SS 316L Flange Test A",
                    "item_type": "Raw Material",
                    "category": "Raw Materials",
                    "uom": "Nos",
                    "unit_cost": 450.0
                },
                {
                    "item_code": f"TEST-ITM-{ts}-2",
                    "item_name": "SS 316L Flange Test B",
                    "item_type": "Raw Material",
                    "category": "Raw Materials",
                    "uom": "Nos",
                    "unit_cost": 550.0
                }
            ],
            id_key="item_code"
        )
        created_items.extend(items)

        # Test Accounting Bank Accounts
        banks = test_module_ordering(
            name="Accounting Bank Accounts",
            list_url="/api/bank-accounts/",
            create_url="/api/bank-accounts/",
            create_payload=[
                {
                    "bank_name": "HDFC Test Bank 1",
                    "account_name": f"UMA HDFC Current A {ts}",
                    "account_number": f"1111222233{ts % 10000}01",
                    "ifsc_code": "HDFC0001234",
                    "branch": "Makarpura",
                    "account_type": "Current",
                    "opening_balance": 100000.0,
                    "current_balance": 100000.0
                },
                {
                    "bank_name": "ICICI Test Bank 2",
                    "account_name": f"UMA ICICI Current B {ts}",
                    "account_number": f"1111222233{ts % 10000}02",
                    "ifsc_code": "ICIC0001234",
                    "branch": "Alkapuri",
                    "account_type": "Current",
                    "opening_balance": 200000.0,
                    "current_balance": 200000.0
                }
            ],
            id_key="id"
        )
        created_banks.extend(banks)

        print("\n=======================================================")
        print("ALL REPRESENTATIVE MODULES PASSED ROW NO. 1 ORDERING!")
        print("=======================================================")

    finally:
        # Clean up test records
        Lead.objects.filter(company_name__startswith="Test ").delete()
        ItemMaster.objects.filter(item_code__startswith="TEST-ITM-").delete()
        BankAccount.objects.filter(account_name__startswith="UMA ").delete()
        print("\nCleaned up test records from database.")
