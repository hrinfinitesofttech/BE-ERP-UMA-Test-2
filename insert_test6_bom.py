import sqlite3
import json
from datetime import datetime

con = sqlite3.connect(r'd:\UMA ERP\BE-ERP-UMA\db.sqlite3')
cur = con.cursor()

test_items = [
    {
        "id": "bi-test6-001",
        "itemNo": 1,
        "itemNumber": "ITM-001",
        "partNumber": "MAT-201",
        "part_number": "MAT-201",
        "itemName": "Mild Steel Plate 5mm (IS 2062 Gr B)",
        "item_name": "Mild Steel Plate 5mm (IS 2062 Gr B)",
        "partName": "Mild Steel Plate 5mm (IS 2062 Gr B)",
        "description": "RAW_MATERIAL for test 6",
        "specification": "IS 2062 Grade B, 5mm thickness structural plate",
        "material": "201 - Mild Steel Plate 5mm",
        "itemType": "Raw Material",
        "item_type": "RAW_MATERIAL",
        "procurement": "PURCHASE",
        "procurementType": "Purchase",
        "quantity": 4.0,
        "qty": 4.0,
        "unit": "KG",
        "estimatedRate": 150.0,
        "estimated_rate": 150.0,
        "rate": 150.0,
        "unitCost": 150.0,
        "unit_price": 150.0,
        "totalEstimatedAmount": 600.0,
        "total_estimated_amount": 600.0,
        "total_amount": 600.0,
        "totalAmount": 600.0,
        "extendedCost": 600.0,
        "makeBrand": "Tata Steel / Jindal"
    },
    {
        "id": "bi-test6-002",
        "itemNo": 2,
        "itemNumber": "ITM-002",
        "partNumber": "MAT-202",
        "part_number": "MAT-202",
        "itemName": "Table Legs 50x50 Box Sub-Assembly",
        "item_name": "Table Legs 50x50 Box Sub-Assembly",
        "partName": "Table Legs 50x50 Box Sub-Assembly",
        "description": "FABRICATED for test 6",
        "specification": "Fabricated 50x50x3mm square hollow section with base flange",
        "material": "202 - Table Legs 50x50 Box Sub-Assembly",
        "itemType": "Fabricated",
        "item_type": "FABRICATED",
        "procurement": "FABRICATE",
        "procurementType": "In-House",
        "quantity": 2.0,
        "qty": 2.0,
        "unit": "PCS",
        "estimatedRate": 850.0,
        "estimated_rate": 850.0,
        "rate": 850.0,
        "unitCost": 850.0,
        "unit_price": 850.0,
        "totalEstimatedAmount": 1700.0,
        "total_estimated_amount": 1700.0,
        "total_amount": 1700.0,
        "totalAmount": 1700.0,
        "extendedCost": 1700.0,
        "makeBrand": "In-House Shopfloor"
    },
    {
        "id": "bi-test6-003",
        "itemNo": 3,
        "itemNumber": "ITM-003",
        "partNumber": "MAT-203",
        "part_number": "MAT-203",
        "itemName": "Heavy Duty Leveling Stud M12",
        "item_name": "Heavy Duty Leveling Stud M12",
        "partName": "Heavy Duty Leveling Stud M12",
        "description": "BOUGHT_OUT for test 6",
        "specification": "M12 x 50mm Galvanized Leveling Bolt with Anti-Vibration Pad",
        "material": "203 - Heavy Duty Leveling Stud M12",
        "itemType": "Bought-Out",
        "item_type": "BOUGHT_OUT",
        "procurement": "PURCHASE",
        "procurementType": "Purchase",
        "quantity": 4.0,
        "qty": 4.0,
        "unit": "PCS",
        "estimatedRate": 320.0,
        "estimated_rate": 320.0,
        "rate": 320.0,
        "unitCost": 320.0,
        "unit_price": 320.0,
        "totalEstimatedAmount": 1280.0,
        "total_estimated_amount": 1280.0,
        "total_amount": 1280.0,
        "totalAmount": 1280.0,
        "extendedCost": 1280.0,
        "makeBrand": "Unbrako / Standard"
    },
    {
        "id": "bi-test6-004",
        "itemNo": 4,
        "itemNumber": "ITM-004",
        "partNumber": "MAT-204",
        "part_number": "MAT-204",
        "itemName": "Anti-Rust Zinc Spray Coating",
        "item_name": "Anti-Rust Zinc Spray Coating",
        "partName": "Anti-Rust Zinc Spray Coating",
        "description": "CONSUMABLE for test 6",
        "specification": "Cold Galvanizing Spray 95% Pure Zinc Primer",
        "material": "204 - Anti-Rust Zinc Spray Coating",
        "itemType": "Consumable",
        "item_type": "CONSUMABLE",
        "procurement": "PURCHASE",
        "procurementType": "Purchase",
        "quantity": 1.0,
        "qty": 1.0,
        "unit": "KG",
        "estimatedRate": 480.0,
        "estimated_rate": 480.0,
        "rate": 480.0,
        "unitCost": 480.0,
        "unit_price": 480.0,
        "totalEstimatedAmount": 480.0,
        "total_estimated_amount": 480.0,
        "total_amount": 480.0,
        "totalAmount": 480.0,
        "extendedCost": 480.0,
        "makeBrand": "CRC / Rust-Oleum"
    }
]

total_cost = sum(i["totalEstimatedAmount"] for i in test_items)
now_str = datetime.now().isoformat()

# Check if test 6 BOM already exists
cur.execute("SELECT id FROM designer_bomheader WHERE id LIKE '%test%6%' OR bom_number LIKE '%test%6%' OR job_number LIKE '%test%6%'")
existing = cur.fetchone()

if existing:
    cur.execute("""
        UPDATE designer_bomheader
        SET items = ?, total_items = ?, total_estimated_cost = ?, updated_at = ?
        WHERE id = ?
    """, (json.dumps(test_items), len(test_items), total_cost, now_str, existing[0]))
    print(f"Updated existing test 6 BOM ({existing[0]}) with {len(test_items)} items!")
else:
    bom_id = "BOM-JOB-TEST-6-V1"
    cur.execute("""
        INSERT INTO designer_bomheader (
            id, bom_number, design_job_id, project_id, job_number,
            active_revision, status, total_items, total_weight_kg,
            total_estimated_cost, prepared_by, approved_by, release_date,
            items, revisions, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bom_id,
        "test 6",
        "DES-2026-TEST-6",
        "PRJ-2026-TEST-6",
        "JOB-TEST-6",
        "V1",
        "draft",
        len(test_items),
        45.0,
        total_cost,
        "Dharmesh Joshi",
        "",
        datetime.now().strftime('%Y-%m-%d'),
        json.dumps(test_items),
        json.dumps([]),
        now_str,
        now_str
    ))
    print(f"Inserted test 6 BOM into database with {len(test_items)} items, total cost: ₹{total_cost}!")

# Also ensure DesignJob for JOB-TEST-6 exists
cur.execute("SELECT id FROM designer_designjob WHERE job_number = 'JOB-TEST-6' OR id LIKE '%TEST-6%'")
if not cur.fetchone():
    cur.execute("""
        INSERT INTO designer_designjob (
            id, design_job_number, project_id, project_number, job_number,
            customer_id, customer_name, customer_po_number, sales_order_number,
            product_name, machine_type, quantity, delivery_date,
            design_manager, assigned_designer, priority, required_date,
            status, remarks, active_revision, approved_by, approved_date,
            disapproved_by, disapproved_date, rejection_reason, approval_notes,
            created_date, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "DES-2026-TEST-6",
        "DES-2026-TEST-6",
        "PRJ-2026-TEST-6",
        "PRJ-2026-TEST-6",
        "JOB-TEST-6",
        "CUST-006",
        "Test 6 Industrial Solutions",
        "PO-TEST-006",
        "SO-TEST-006",
        "test 6 - Custom Machine Assembly",
        "Heavy Fabrication",
        1,
        "2026-10-31",
        "Ketan Patel",
        "Dharmesh Joshi",
        "high",
        "2026-10-25",
        "in_progress",
        "Master BOM test 6 created with components",
        "V1",
        "", "", "", "", "", "",
        datetime.now().strftime('%Y-%m-%d'),
        now_str,
        now_str
    ))
    print("Created linked DesignJob DES-2026-TEST-6 for JOB-TEST-6 in database!")

con.commit()

# Print current BOMs in database
rows = cur.execute("SELECT id, bom_number, job_number, active_revision, total_items, total_estimated_cost FROM designer_bomheader").fetchall()
print("\nAll BOMs now in database:")
for r in rows:
    print(f"  ID: {r[0]} | BOM Number: {r[1]} | Job: {r[2]} | Rev: {r[3]} | Items: {r[4]} | Total: ₹{r[5]}")

con.close()
