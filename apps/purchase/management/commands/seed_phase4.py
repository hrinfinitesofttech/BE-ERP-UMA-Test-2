from django.core.management.base import BaseCommand
from apps.purchase.models import Supplier, PurchaseOrder
from apps.store.models import (
    ItemCategory,
    UOMMaster,
    ItemMaster,
    Warehouse,
    GoodsReceiptNote,
    QCInspection,
    StockBalance,
    StockLedgerEntry,
)


class Command(BaseCommand):
    help = 'Seeds initial Purchase and Store/Inventory data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Phase 4 Purchase & Store Data Seeding...'))

        # 1. Suppliers
        suppliers_data = [
            {
                'id': 'SUP-001',
                'vendor_code': 'VEN-001',
                'name': 'Jindal Stainless Limited',
                'category': 'Raw Material',
                'supplier_type': 'Manufacturer',
                'contact_person': 'Ramesh Singhal',
                'mobile': '+91 98110 55443',
                'email': 'plates.sales@jindalstainless.com',
                'address': 'Jindal Center, 12 Bhikaiji Cama Place',
                'city': 'New Delhi',
                'state': 'Delhi',
                'country': 'India',
                'pincode': '110066',
                'gstin': '07AAACJ1234F1Z0',
                'pan': 'AAACJ1234F',
                'payment_terms': '30 Days Credit',
                'rating': 4.9,
                'status': 'active',
            },
            {
                'id': 'SUP-002',
                'vendor_code': 'VEN-002',
                'name': 'ABB India Limited',
                'category': 'Bought-out Items',
                'supplier_type': 'Manufacturer',
                'contact_person': 'Vinay Kulkarni',
                'mobile': '+91 98200 44332',
                'email': 'motors.india@abb.com',
                'address': 'Maneja Works, Post Box No. 37',
                'city': 'Vadodara',
                'state': 'Gujarat',
                'country': 'India',
                'pincode': '390013',
                'gstin': '24AAACA1234E1Z8',
                'pan': 'AAACA1234E',
                'payment_terms': '30% Advance, 70% ag. PI',
                'rating': 4.8,
                'status': 'active',
            },
            {
                'id': 'SUP-003',
                'vendor_code': 'VEN-003',
                'name': 'EagleBurgmann India Pvt. Ltd.',
                'category': 'Bought-out Items',
                'supplier_type': 'Manufacturer',
                'contact_person': 'Makarand Joshi',
                'mobile': '+91 98220 99881',
                'email': 'sales@in.eagleburgmann.com',
                'address': 'Plot 644, Star Park, Wagholi',
                'city': 'Pune',
                'state': 'Maharashtra',
                'country': 'India',
                'pincode': '412207',
                'gstin': '27AAACE1234H1Z4',
                'pan': 'AAACE1234H',
                'payment_terms': '45 Days Credit',
                'rating': 4.7,
                'status': 'active',
            },
            {
                'id': 'SUP-004',
                'vendor_code': 'VEN-004',
                'name': 'Ratnamani Metals & Tubes Ltd.',
                'category': 'Raw Material',
                'supplier_type': 'Manufacturer',
                'contact_person': 'Suresh Patel',
                'mobile': '+91 98250 88776',
                'email': 'tubes@ratnamani.com',
                'address': '17, Rajnagar Society, Usmanpura',
                'city': 'Ahmedabad',
                'state': 'Gujarat',
                'country': 'India',
                'pincode': '380014',
                'gstin': '24AAACR1234L1Z9',
                'pan': 'AAACR1234L',
                'payment_terms': '30 Days Credit',
                'rating': 4.8,
                'status': 'active',
            },
        ]
        for sup in suppliers_data:
            Supplier.objects.update_or_create(id=sup['id'], defaults=sup)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(suppliers_data)} Suppliers seeded.'))

        # 2. Categories & UOMs
        cat_data = [
            {'id': 'cat-rm', 'name': 'Raw Material', 'code': 'RM', 'description': 'Steel plates, forgings, pipes, rounds'},
            {'id': 'cat-bo', 'name': 'Bought-Out Items', 'code': 'BO', 'description': 'Motors, seals, valves, gearboxes'},
            {'id': 'cat-cons', 'name': 'Consumables', 'code': 'CONS', 'description': 'Welding wire, grinding wheels, gases'},
            {'id': 'cat-fg', 'name': 'Finished Goods', 'code': 'FG', 'description': 'Completed pressure vessels and equipment'},
        ]
        for c in cat_data:
            ItemCategory.objects.update_or_create(id=c['id'], defaults=c)

        uom_data = [
            {'id': 'uom-kg', 'name': 'Kilogram', 'code': 'Kg', 'description': 'Weight in Kilograms'},
            {'id': 'uom-mtr', 'name': 'Meter', 'code': 'Mtr', 'description': 'Length in Meters'},
            {'id': 'uom-nos', 'name': 'Numbers', 'code': 'Nos', 'description': 'Item Count'},
            {'id': 'uom-set', 'name': 'Set', 'code': 'Set', 'description': 'Assembly Set'},
        ]
        for u in uom_data:
            UOMMaster.objects.update_or_create(id=u['id'], defaults=u)
        self.stdout.write(self.style.SUCCESS('[OK] Item Categories & UOMs seeded.'))

        # 3. Item Master
        items_data = [
            {
                'id': 'itm-rm-ss316l-8mm',
                'item_code': 'RM-SS316L-PL-8MM',
                'item_name': 'SS 316L Plates (8mm thk, SA 240)',
                'item_type': 'Raw Material',
                'category': 'Raw Material',
                'sub_category': 'Plates',
                'description': 'Hot rolled, solution annealed and pickled SS 316L plate for vessel shell.',
                'specification': 'ASTM A240 / ASME SA 240 Gr 316L with 3.1 Mill Test Certificate',
                'brand_make': 'Jindal Stainless',
                'hsn_sac': '7219',
                'gst_rate': 18.0,
                'uom': 'Kg',
                'minimum_stock': 500,
                'maximum_stock': 5000,
                'reorder_level': 1000,
                'unit_cost': 345,
                'status': 'Active',
            },
            {
                'id': 'itm-rm-ss316l-10mm',
                'item_code': 'RM-SS316L-PL-10MM',
                'item_name': 'SS 316L Plates (10mm thk, SA 240)',
                'item_type': 'Raw Material',
                'category': 'Raw Material',
                'sub_category': 'Plates',
                'description': 'Heavy 10mm SS 316L plate for dish ends and flange blanks.',
                'specification': 'SA 240 Gr 316L, NACE MR0175 compliant',
                'brand_make': 'Jindal Stainless',
                'hsn_sac': '7219',
                'gst_rate': 18.0,
                'uom': 'Kg',
                'minimum_stock': 500,
                'maximum_stock': 4000,
                'reorder_level': 800,
                'unit_cost': 355,
                'status': 'Active',
            },
            {
                'id': 'itm-bo-mtr-15hp',
                'item_code': 'BO-MTR-15HP-FLP',
                'item_name': 'ABB 15 HP Flameproof Electric Motor',
                'item_type': 'Bought-Out Item',
                'category': 'Bought-Out Items',
                'sub_category': 'Electrical Drives',
                'description': '15 HP (11 kW), 4 Pole, 1440 RPM, Foot Mounted Flameproof Motor (Ex d IIC T4).',
                'specification': 'IS/IEC 60079-1, PESO certified, IP55, Class F insulation',
                'brand_make': 'ABB India',
                'hsn_sac': '8501',
                'gst_rate': 18.0,
                'uom': 'Nos',
                'minimum_stock': 1,
                'maximum_stock': 5,
                'reorder_level': 2,
                'unit_cost': 145000,
                'status': 'Active',
            },
            {
                'id': 'itm-bo-seal-dual',
                'item_code': 'BO-SEAL-DUAL-75MM',
                'item_name': 'Burgmann Dual Mechanical Seal with Pot',
                'item_type': 'Bought-Out Item',
                'category': 'Bought-Out Items',
                'sub_category': 'Mechanical Seals',
                'description': 'Top entry cartridge type dual mechanical seal for agitator shaft Dia 75mm.',
                'specification': 'Faces: Silicon Carbide vs Tungsten Carbide, Elastomer: FFKM Kalrez',
                'brand_make': 'EagleBurgmann',
                'hsn_sac': '8484',
                'gst_rate': 18.0,
                'uom': 'Set',
                'minimum_stock': 1,
                'maximum_stock': 4,
                'reorder_level': 1,
                'unit_cost': 285000,
                'status': 'Active',
            },
        ]
        for itm in items_data:
            ItemMaster.objects.update_or_create(id=itm['id'], defaults=itm)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(items_data)} Item Masters seeded.'))

        # 4. Warehouses
        warehouses_data = [
            {
                'id': 'wh-main',
                'warehouse_code': 'WH-MAIN',
                'name': 'Main Raw Material & Plate Yard',
                'warehouse_type': 'Raw Material Store',
                'location': 'Makarpura Bay 1 & Bay 2',
                'incharge': 'Hitesh Rawal',
                'status': 'Active',
            },
            {
                'id': 'wh-bo',
                'warehouse_code': 'WH-BO',
                'name': 'Bought-Out & Hardware Store',
                'warehouse_type': 'Component Store',
                'location': 'Makarpura Mezzanine Store',
                'incharge': 'Rajesh Parmar',
                'status': 'Active',
            },
        ]
        for wh in warehouses_data:
            Warehouse.objects.update_or_create(id=wh['id'], defaults=wh)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(warehouses_data)} Warehouses seeded.'))

        # 5. Purchase Order
        po_items = [
            {'itemCode': 'RM-SS316L-PL-8MM', 'itemName': 'SS 316L Plates (8mm thk, SA 240)', 'quantity': 1850, 'unit': 'Kg', 'rate': 345, 'amount': 638250},
        ]
        po, _ = PurchaseOrder.objects.update_or_create(
            id='PO-2026-0042',
            defaults={
                'po_number': 'PO-2026-0042',
                'date': '2026-08-14',
                'supplier_id': 'SUP-001',
                'supplier_name': 'Jindal Stainless Limited',
                'contact_person': 'Ramesh Singhal',
                'project_id': 'PRJ-2026-0042',
                'job_code': 'JOB-2026-0042',
                'delivery_date': '2026-09-02',
                'payment_terms': '30 Days Credit',
                'items': po_items,
                'sub_total': 638250,
                'tax_amount': 114885,
                'grand_total': 753135,
                'status': 'fully_received',
                'prepared_by': 'Vikram Solanki',
                'approved_by': 'Rajesh Patel',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'[OK] Purchase Order {po.po_number} seeded.'))

        # 6. Goods Receipt Note (GRN) & Inward QC Inspection
        grn_items = [
            {
                'itemCode': 'RM-SS316L-PL-8MM',
                'itemName': 'SS 316L Plates (8mm thk, SA 240)',
                'heatNumber': 'HT-88912-JSL',
                'orderedQty': 1850,
                'receivedQty': 1850,
                'acceptedQty': 1850,
                'rejectedQty': 0,
                'unitRate': 345,
                'amount': 638250,
            }
        ]
        grn, _ = GoodsReceiptNote.objects.update_or_create(
            id='GRN-2026-0018',
            defaults={
                'grn_number': 'GRN-2026-0018',
                'date': '2026-09-02',
                'po_id': po.id,
                'po_number': po.po_number,
                'supplier_id': po.supplier_id,
                'supplier_name': po.supplier_name,
                'challan_number': 'CH/JSL/2026/991',
                'challan_date': '2026-09-01',
                'invoice_number': 'INV/JSL/26/10294',
                'invoice_date': '2026-09-01',
                'vehicle_number': 'GJ-06-AX-4821',
                'received_by': 'Hitesh Rawal',
                'warehouse_id': 'wh-main',
                'items': grn_items,
                'status': 'Accepted',
                'qc_status': 'Pass',
                'notes': 'Chemical analysis and mechanical properties verified against MTC HT-88912-JSL. Dimension verified 8.05mm.',
            }
        )

        QCInspection.objects.update_or_create(
            id='QC-2026-0018',
            defaults={
                'grn_id': grn.id,
                'grn_number': grn.grn_number,
                'inspection_date': '2026-09-03',
                'inspector': 'Ketan Patel',
                'items': [
                    {'parameter': 'Chemical Composition (Ni 12.1%, Cr 16.8%, Mo 2.1%)', 'observed': 'Conforms to SA 240 316L', 'result': 'Pass'},
                    {'parameter': 'Ultrasonic Thickness Check', 'observed': '8.02mm to 8.08mm', 'result': 'Pass'},
                    {'parameter': 'Surface Finish & Visual Pitting Check', 'observed': 'No visual defects, mill scale clear', 'result': 'Pass'},
                ],
                'overall_result': 'Pass',
                'remarks': '100% Cleared for cutting and fabrication in Job JOB-2026-0042.',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'[OK] GRN {grn.grn_number} and Inward QC seeded.'))

        # 7. Stock Balance & Stock Ledger
        bal, _ = StockBalance.objects.update_or_create(
            id='stk-rm-ss316l-pl-8mm',
            defaults={
                'item_id': 'itm-rm-ss316l-8mm',
                'item_code': 'RM-SS316L-PL-8MM',
                'item_name': 'SS 316L Plates (8mm thk, SA 240)',
                'category': 'Raw Material',
                'uom': 'Kg',
                'warehouse_id': 'wh-main',
                'warehouse_name': 'Main Raw Material & Plate Yard',
                'location': 'Rack A / Plate Bay 2',
                'quantity': 1850,
                'reserved_quantity': 1850, # Reserved for JOB-2026-0042
                'available_quantity': 0,
                'unit_rate': 345,
                'total_value': 638250,
            }
        )

        StockLedgerEntry.objects.update_or_create(
            id='ledg-grn-2026-0018-rm-ss316l-pl-8mm',
            defaults={
                'date': '2026-09-02',
                'transaction_type': 'GRN',
                'reference_number': grn.grn_number,
                'item_id': 'itm-rm-ss316l-8mm',
                'item_code': 'RM-SS316L-PL-8MM',
                'item_name': 'SS 316L Plates (8mm thk, SA 240)',
                'warehouse_id': 'wh-main',
                'inward_quantity': 1850,
                'outward_quantity': 0,
                'closing_quantity': 1850,
                'unit_rate': 345,
                'total_amount': 638250,
                'performed_by': 'Hitesh Rawal',
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Stock Balance and Perpetual Stock Ledger seeded.'))
        self.stdout.write(self.style.SUCCESS('Done: Phase 4 Purchase & Store Seeding Complete!'))
