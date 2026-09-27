from django.core.management.base import BaseCommand
from datetime import date, timedelta
from apps.production.models import (
    ManufacturingJob, ProductionPlan, WorkCenter, RoutingOperation,
    WorkOrder, ProductionOrder, ProductionScheduleItem, ProductionEntry,
    WIPRecord, ProductionHold, ReworkOrder, ProductionScrap, FinishedGoodsItem
)
from apps.maintenance.models import (
    InternalAsset, CustomerMachine, ServiceRequest, PreventiveMaintenancePlan,
    BreakdownRecord, ServiceVisit, AMCContract
)
from apps.hr.models import (
    Designation, EmployeeDocument, ShiftMaster, AttendanceRecord,
    LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization,
    OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure,
    PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense
)


class Command(BaseCommand):
    help = 'Seeds Phase 5 data (Production Execution, Maintenance & Plant Service, HR & Payroll)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Phase 5: Production, Maintenance & HR...')

        today = date.today()

        # -------------------------------------------------------------
        # 1. PRODUCTION & SHOPFLOOR SEEDING
        # -------------------------------------------------------------
        self.stdout.write('  Seeding Work Centers...')
        work_centers_data = [
            {
                'id': 'WC-01',
                'work_center_code': 'WC-PLASMA-01',
                'work_center_name': 'CNC High-Definition Plasma & Oxy Cutting Bay',
                'department': 'Fabrication Prep',
                'machine_name': 'Messer MultiTherm 4000 CNC Plasma',
                'machine_number': 'CUT-M-01',
                'location': 'Shop Bay 1 - North Wing',
                'capacity_per_day_hours': 16.0,
                'available_hours': 14.5,
                'efficiency_percent': 92.5,
                'supervisor_name': 'Vikram Rathore',
                'status': 'Running'
            },
            {
                'id': 'WC-02',
                'work_center_code': 'WC-ROLL-01',
                'work_center_name': 'Hydraulic 4-Roll Plate Bending Machine Bay',
                'department': 'Rolling & Forming',
                'machine_name': 'Davi MCB 4-Roll 70mm Plate Rolling Machine',
                'machine_number': 'FORM-R-01',
                'location': 'Shop Bay 1 - Center',
                'capacity_per_day_hours': 16.0,
                'available_hours': 16.0,
                'efficiency_percent': 95.0,
                'supervisor_name': 'Vikram Rathore',
                'status': 'Available'
            },
            {
                'id': 'WC-03',
                'work_center_code': 'WC-SAW-01',
                'work_center_name': 'Heavy Column & Boom Submerged Arc Welding (SAW) Station',
                'department': 'Welding Bay',
                'machine_name': 'Lincoln Power Wave AC/DC 1000 SAW Manipulator',
                'machine_number': 'WELD-SAW-01',
                'location': 'Shop Bay 2 - South Wing',
                'capacity_per_day_hours': 20.0,
                'available_hours': 18.0,
                'efficiency_percent': 90.0,
                'supervisor_name': 'Rajesh Patel',
                'status': 'Running'
            },
            {
                'id': 'WC-04',
                'work_center_code': 'WC-BORING-01',
                'work_center_name': 'Heavy CNC Floor Horizontal Boring & Milling Bay',
                'department': 'Machining',
                'machine_name': 'Toshiba BP-150 Floor Type CNC Boring Machine',
                'machine_number': 'MCH-BOR-01',
                'location': 'Machine Shop Bay 3',
                'capacity_per_day_hours': 16.0,
                'available_hours': 12.0,
                'efficiency_percent': 88.0,
                'supervisor_name': 'Manoj Sharma',
                'status': 'Running'
            },
            {
                'id': 'WC-05',
                'work_center_code': 'WC-TEST-01',
                'work_center_name': 'Hydrostatic Testing & NDT Bunker',
                'department': 'Quality Control & Testing',
                'machine_name': 'High Pressure Triplex Plunger Hydro Pump 700 Bar',
                'machine_number': 'QC-HYD-01',
                'location': 'Testing Bunker Yard',
                'capacity_per_day_hours': 12.0,
                'available_hours': 10.0,
                'efficiency_percent': 98.0,
                'supervisor_name': 'Kavita Iyer',
                'status': 'Available'
            },
        ]
        for wc in work_centers_data:
            WorkCenter.objects.update_or_create(id=wc['id'], defaults=wc)

        self.stdout.write('  Seeding Routing Operations...')
        operations_data = [
            {
                'id': 'OP-10',
                'operation_number': 10,
                'operation_name': 'Raw Material Profiling & Plate CNC Plasma Cutting',
                'sequence': 1,
                'work_center_code': 'WC-PLASMA-01',
                'work_center_name': 'CNC Plasma Bay',
                'machine_name': 'Messer MultiTherm 4000',
                'department': 'Fabrication Prep',
                'planned_setup_minutes': 45,
                'planned_processing_minutes': 360,
                'total_planned_minutes': 405,
                'assigned_operator': 'Dinesh Verma',
                'qc_required': True,
                'instructions': 'Check shell plate diagonals within +/- 1.0mm tolerance.',
                'status': 'Completed'
            },
            {
                'id': 'OP-20',
                'operation_number': 20,
                'operation_name': 'Plate Edge Beveling & 4-Roll Shell Rolling',
                'sequence': 2,
                'work_center_code': 'WC-ROLL-01',
                'work_center_name': 'Plate Bending Bay',
                'machine_name': 'Davi MCB 4-Roll',
                'department': 'Rolling & Forming',
                'planned_setup_minutes': 60,
                'planned_processing_minutes': 480,
                'total_planned_minutes': 540,
                'assigned_operator': 'Suresh Kumar',
                'qc_required': True,
                'instructions': 'Ensure out-of-roundness ovality check is below 0.5% of ID.',
                'status': 'Completed'
            },
            {
                'id': 'OP-30',
                'operation_number': 30,
                'operation_name': 'Longitudinal & Circumferential SAW Seam Welding',
                'sequence': 3,
                'work_center_code': 'WC-SAW-01',
                'work_center_name': 'SAW Station',
                'machine_name': 'Lincoln Power Wave 1000',
                'department': 'Welding Bay',
                'planned_setup_minutes': 90,
                'planned_processing_minutes': 720,
                'total_planned_minutes': 810,
                'assigned_operator': 'Kishore Jha',
                'qc_required': True,
                'instructions': 'Interpass temp 150-200C. Pre-heat required. 100% UT/RT after welding.',
                'status': 'In Progress'
            },
            {
                'id': 'OP-40',
                'operation_number': 40,
                'operation_name': 'Flange Facing & Nozzle Bore CNC Machining',
                'sequence': 4,
                'work_center_code': 'WC-BORING-01',
                'work_center_name': 'CNC Boring Bay',
                'machine_name': 'Toshiba BP-150',
                'department': 'Machining',
                'planned_setup_minutes': 120,
                'planned_processing_minutes': 300,
                'total_planned_minutes': 420,
                'assigned_operator': 'Ramesh Suthar',
                'qc_required': True,
                'instructions': 'Serrated spiral finish on ASME B16.5 flange face Ra 3.2-6.3 um.',
                'status': 'Pending'
            },
            {
                'id': 'OP-50',
                'operation_number': 50,
                'operation_name': 'Hydrostatic Pressure Proof Test & Final Blasting/Painting',
                'sequence': 5,
                'work_center_code': 'WC-TEST-01',
                'work_center_name': 'Testing Bunker Yard',
                'machine_name': 'Hydro Pump 700 Bar',
                'department': 'Quality Control & Testing',
                'planned_setup_minutes': 60,
                'planned_processing_minutes': 240,
                'total_planned_minutes': 300,
                'assigned_operator': 'Ashok Prajapati',
                'qc_required': True,
                'instructions': 'Test pressure 36.4 Bar hold for 120 mins. Zero pressure drop permissible.',
                'status': 'Pending'
            },
        ]
        for op in operations_data:
            RoutingOperation.objects.update_or_create(id=op['id'], defaults=op)

        self.stdout.write('  Seeding Manufacturing Jobs...')
        mfg_jobs = [
            {
                'id': 'MJ-2026-001',
                'job_number': 'JOB-2026-001',
                'project_id': 'PRJ-2026-001',
                'project_number': 'PRJ-2026-001',
                'customer_id': 'CUST-001',
                'customer_name': 'Reliance Industries Limited (Jamnagar)',
                'sales_order_id': 'SO-2026-001',
                'sales_order_number': 'SO-2026-001',
                'customer_po_number': 'RIL/PO/450098231',
                'product_name': 'High Pressure Hydrogen De-Sulphurization Reactor (50 KL)',
                'specification': 'ASME Sec VIII Div 2, SA 387 Gr 11 Cl 2 + SS347 Weld Overlay, 45mm Shell, 420C @ 28 Bar',
                'quantity': 1.0,
                'unit': 'Unit',
                'design_id': 'DES-2026-001',
                'design_revision': 'R2',
                'bom_id': 'BOM-2026-001',
                'bom_revision': 'R2',
                'project_manager': 'Priya Nair',
                'production_manager': 'Vikram Rathore',
                'planned_start_date': today - timedelta(days=20),
                'planned_completion_date': today + timedelta(days=40),
                'actual_start_date': today - timedelta(days=18),
                'production_progress': 65,
                'status': 'In Production'
            },
            {
                'id': 'MJ-2026-002',
                'job_number': 'JOB-2026-002',
                'project_id': 'PRJ-2026-002',
                'project_number': 'PRJ-2026-002',
                'customer_id': 'CUST-002',
                'customer_name': 'Larsen & Toubro Heavy Engineering (Hazira)',
                'sales_order_id': 'SO-2026-002',
                'sales_order_number': 'SO-2026-002',
                'customer_po_number': 'LT-HE-P8812',
                'product_name': 'Cryogenic Liquid Nitrogen Storage Tank 100 KL (Double Walled)',
                'specification': 'EN 13458, Inner Vessel SA 240 Gr 304L, Outer C-Steel SA 516 Gr 70 with Perlite Vacuum insulation',
                'quantity': 2.0,
                'unit': 'Nos',
                'design_id': 'DES-2026-002',
                'design_revision': 'R1',
                'bom_id': 'BOM-2026-002',
                'bom_revision': 'R1',
                'project_manager': 'Priya Nair',
                'production_manager': 'Vikram Rathore',
                'planned_start_date': today - timedelta(days=10),
                'planned_completion_date': today + timedelta(days=50),
                'actual_start_date': today - timedelta(days=8),
                'production_progress': 30,
                'status': 'In Production'
            },
            {
                'id': 'MJ-2026-003',
                'job_number': 'JOB-2026-003',
                'project_id': 'PRJ-2026-003',
                'project_number': 'PRJ-2026-003',
                'customer_id': 'CUST-003',
                'customer_name': 'Adani Ports & SEZ Ltd (Mundra)',
                'sales_order_id': 'SO-2026-003',
                'sales_order_number': 'SO-2026-003',
                'customer_po_number': 'APSEZ/MECH/2026/089',
                'product_name': 'Bulk Material Handling Ship Loader Boom Structure (42m Reach)',
                'specification': 'IS 2062 E350BR Structural Box Girders, Hot Dip Galvanized & 3-Coat Marine Epoxy',
                'quantity': 1.0,
                'unit': 'Set',
                'design_id': 'DES-2026-003',
                'design_revision': 'R0',
                'bom_id': 'BOM-2026-003',
                'bom_revision': 'R0',
                'project_manager': 'Amit Verma',
                'production_manager': 'Vikram Rathore',
                'planned_start_date': today + timedelta(days=5),
                'planned_completion_date': today + timedelta(days=75),
                'production_progress': 5,
                'status': 'Planning'
            }
        ]
        for mj in mfg_jobs:
            ManufacturingJob.objects.update_or_create(id=mj['id'], defaults=mj)

        self.stdout.write('  Seeding Work Orders & Production Entries...')
        WorkOrder.objects.update_or_create(
            id='WO-2026-001-A',
            defaults={
                'work_order_number': 'WO-2026-001-A',
                'job_id': 'MJ-2026-001',
                'job_number': 'JOB-2026-001',
                'project_id': 'PRJ-2026-001',
                'customer_id': 'CUST-001',
                'customer_name': 'Reliance Industries Limited (Jamnagar)',
                'sales_order_number': 'SO-2026-001',
                'design_revision': 'R2',
                'bom_revision': 'R2',
                'product_name': 'High Pressure Hydrogen De-Sulphurization Reactor (50 KL)',
                'production_quantity': 1.0,
                'uom': 'Unit',
                'planned_start_date': today - timedelta(days=20),
                'planned_end_date': today + timedelta(days=40),
                'actual_start_date': today - timedelta(days=18),
                'production_manager': 'Vikram Rathore',
                'priority': 'High',
                'status': 'Released',
                'remarks': 'Priority client order. Strict inspection holding points.'
            }
        )

        ProductionOrder.objects.update_or_create(
            id='PO-PROD-2026-001',
            defaults={
                'production_order_number': 'PO-PROD-2026-001',
                'work_order_id': 'WO-2026-001-A',
                'work_order_number': 'WO-2026-001-A',
                'job_id': 'MJ-2026-001',
                'job_number': 'JOB-2026-001',
                'product_name': 'Reactor Shell Course 1 & 2 Assembly',
                'quantity': 1.0,
                'bom_revision': 'R2',
                'design_revision': 'R2',
                'planned_start_date': today - timedelta(days=15),
                'planned_end_date': today + timedelta(days=10),
                'actual_start_date': today - timedelta(days=14),
                'production_manager': 'Vikram Rathore',
                'status': 'In Progress'
            }
        )

        ProductionEntry.objects.update_or_create(
            id='PENTRY-2026-0001',
            defaults={
                'production_entry_number': 'PENTRY-2026-0001',
                'entry_date': today - timedelta(days=1),
                'job_id': 'MJ-2026-001',
                'job_number': 'JOB-2026-001',
                'work_order_number': 'WO-2026-001-A',
                'production_order_number': 'PO-PROD-2026-001',
                'operation_name': 'Longitudinal & Circumferential SAW Seam Welding',
                'work_center_name': 'SAW Station',
                'machine_name': 'Lincoln Power Wave 1000',
                'operator_name': 'Kishore Jha',
                'start_time': '09:00',
                'end_time': '17:30',
                'planned_quantity': 1.0,
                'produced_quantity': 1.0,
                'rejected_quantity': 0.0,
                'rework_quantity': 0.0,
                'scrap_quantity': 0.0,
                'good_quantity': 1.0,
                'downtime_minutes': 30,
                'downtime_reason': 'Pre-heat torch burner hose replacement',
                'remarks': 'First shell pass complete, 100% visual and preliminary UT clear.',
                'created_by': 'Vikram Rathore'
            }
        )

        WIPRecord.objects.update_or_create(
            id='WIP-2026-001',
            defaults={
                'job_id': 'MJ-2026-001',
                'job_number': 'JOB-2026-001',
                'work_order_number': 'WO-2026-001-A',
                'production_order_number': 'PO-PROD-2026-001',
                'current_operation_name': 'Longitudinal & Circumferential SAW Seam Welding',
                'completed_operations_count': 2,
                'total_operations_count': 5,
                'wip_quantity': 1.0,
                'uom': 'Unit',
                'location': 'Shop Floor Bay 2 - Welding Bed 3',
                'responsible_department': 'Welding Bay',
                'start_date': today - timedelta(days=18),
                'expected_completion_date': today + timedelta(days=40),
                'delay_days': 0,
                'status': 'In Progress'
            }
        )

        FinishedGoodsItem.objects.update_or_create(
            id='FG-2026-001',
            defaults={
                'finished_goods_number': 'FG-2026-001',
                'job_id': 'MJ-2026-000',
                'job_number': 'JOB-2025-098',
                'work_order_number': 'WO-2025-098-A',
                'production_order_number': 'PO-PROD-2025-098',
                'product_name': 'Industrial Shell & Tube Heat Exchanger (HE-200)',
                'specification': 'TEMA-R, Carbon Steel Shell, 1200 SS 316L Tubes, 25 Bar',
                'quantity': 1.0,
                'uom': 'Nos',
                'serial_number': 'UMA-HE-2026-042',
                'batch_number': 'BATCH-2026-Q1',
                'warehouse_id': 'WH-FG-01',
                'warehouse_name': 'Finished Goods Yard & Dispatch Dock',
                'location_bin': 'FG-DOCK-B1',
                'completion_date': today - timedelta(days=5),
                'qc_status': 'QC Passed',
                'status': 'Ready for Dispatch'
            }
        )

        # -------------------------------------------------------------
        # 2. MAINTENANCE & PLANT SERVICE SEEDING
        # -------------------------------------------------------------
        self.stdout.write('  Seeding Internal Plant Assets...')
        internal_assets = [
            {
                'id': 'AST-101',
                'asset_code': 'AST-CNC-001',
                'asset_name': 'Messer MultiTherm 4000 CNC High Definition Plasma Cutter',
                'asset_type': 'Machine',
                'category': 'CNC Thermal Cutting',
                'manufacturer': 'Messer Cutting Systems GmbH',
                'model': 'MultiTherm 4000',
                'serial_number': 'MT4000-GER-98124',
                'purchase_date': today - timedelta(days=730),
                'purchase_supplier': 'Messer India Corp Pvt Ltd',
                'purchase_invoice': 'INV-MSR-4512',
                'purchase_cost': 8500000.0,
                'installation_date': today - timedelta(days=710),
                'location': 'Shop Floor Bay 1 - North Wing',
                'department': 'Fabrication Prep',
                'responsible_person': 'Vikram Rathore',
                'warranty_start': today - timedelta(days=710),
                'warranty_end': today - timedelta(days=345),
                'amc_status': 'Active',
                'amc_start': today - timedelta(days=340),
                'amc_end': today + timedelta(days=25),
                'maintenance_frequency': 'Monthly',
                'criticality': 'Critical',
                'status': 'Active',
                'documents': []
            },
            {
                'id': 'AST-102',
                'asset_code': 'AST-ROLL-001',
                'asset_name': 'Davi MCB 4-Roll 70mm Capacity Plate Bending Machine',
                'asset_type': 'Machine',
                'category': 'Plate Rolling & Forming',
                'manufacturer': 'Promau Davi S.r.l. Italy',
                'model': 'MCB 3070',
                'serial_number': 'DAVI-IT-77412',
                'purchase_date': today - timedelta(days=1200),
                'purchase_supplier': 'Davi Asia Pacific',
                'purchase_invoice': 'INV-DAVI-8812',
                'purchase_cost': 14200000.0,
                'installation_date': today - timedelta(days=1180),
                'location': 'Shop Floor Bay 1 - Center',
                'department': 'Rolling & Forming',
                'responsible_person': 'Vikram Rathore',
                'warranty_start': today - timedelta(days=1180),
                'warranty_end': today - timedelta(days=815),
                'amc_status': 'Active',
                'amc_start': today - timedelta(days=180),
                'amc_end': today + timedelta(days=185),
                'maintenance_frequency': 'Quarterly',
                'criticality': 'Critical',
                'status': 'Active',
                'documents': []
            },
            {
                'id': 'AST-103',
                'asset_code': 'AST-CRN-001',
                'asset_name': 'Demag Double Girder Heavy EOT Crane (50T / 15T Aux)',
                'asset_type': 'Equipment',
                'category': 'Material Handling Crane',
                'manufacturer': 'Terex Demag Cranes India',
                'model': 'ZKKE 50T-24M',
                'serial_number': 'DMG-CRN-2023-019',
                'purchase_date': today - timedelta(days=1000),
                'purchase_supplier': 'Demag Cranes & Components India Pvt Ltd',
                'purchase_invoice': 'INV-DMG-099',
                'purchase_cost': 9800000.0,
                'installation_date': today - timedelta(days=980),
                'location': 'Shop Floor Bay 2 High Bay',
                'department': 'Material Handling',
                'responsible_person': 'Manoj Sharma',
                'warranty_start': today - timedelta(days=980),
                'warranty_end': today - timedelta(days=615),
                'amc_status': 'Active',
                'amc_start': today - timedelta(days=200),
                'amc_end': today + timedelta(days=165),
                'maintenance_frequency': 'Monthly',
                'criticality': 'Critical',
                'status': 'Active',
                'documents': []
            },
        ]
        for asset in internal_assets:
            InternalAsset.objects.update_or_create(id=asset['id'], defaults=asset)

        self.stdout.write('  Seeding Customer Installed Machines & Service Requests...')
        cust_machine = {
            'id': 'CM-2026-001',
            'customer_machine_id': 'CM-2026-001',
            'customer_id': 'CUST-001',
            'customer_name': 'Reliance Industries Limited (Jamnagar)',
            'project_id': 'PRJ-2025-088',
            'project_name': 'Jamnagar DTA Refinery Expansion Phase II',
            'job_id': 'JOB-2025-088',
            'job_number': 'JOB-2025-088',
            'sales_order_id': 'SO-2025-088',
            'customer_po': 'RIL/EXP/2025/1102',
            'dispatch_number': 'DISP-2025-045',
            'installation_number': 'INST-2025-032',
            'machine_name': 'High Pressure Autoclave Reactor 50 KL',
            'machine_model': 'AUTOCLAVE-HP-50KL',
            'serial_number': 'UMA-RIL-AC-01',
            'manufacturing_date': today - timedelta(days=220),
            'installation_date': today - timedelta(days=180),
            'commissioning_date': today - timedelta(days=165),
            'warranty_start': today - timedelta(days=165),
            'warranty_end': today + timedelta(days=200),
            'amc_start': today - timedelta(days=165),
            'amc_end': today + timedelta(days=200),
            'machine_location': 'Block C - Petrochem Unit 4, Jamnagar Complex',
            'customer_contact': 'Dr. Alok Nath (Lead Plant Engineer)',
            'contact_phone': '+91 98250 11922',
            'contact_email': 'alok.nath@ril.com',
            'service_engineer': 'Sanjay Mehta',
            'status': 'Installed & Operational',
            'documents': []
        }
        CustomerMachine.objects.update_or_create(id=cust_machine['id'], defaults=cust_machine)

        ServiceRequest.objects.update_or_create(
            id='SR-2026-001',
            defaults={
                'request_number': 'SR-2026-001',
                'request_date': today - timedelta(days=3),
                'origin': 'Customer',
                'customer_id': 'CUST-001',
                'customer_name': 'Reliance Industries Limited (Jamnagar)',
                'customer_machine_id': 'CM-2026-001',
                'machine_name': 'High Pressure Autoclave Reactor 50 KL',
                'serial_number': 'UMA-RIL-AC-01',
                'job_number': 'JOB-2025-088',
                'contact_person': 'Dr. Alok Nath',
                'mobile': '+91 98250 11922',
                'email': 'alok.nath@ril.com',
                'complaint_type': 'Mechanical Seal Minor Leakage Under Cyclic Load',
                'description': 'Customer reported minor lubricant drop and secondary seal pressure drop during thermal cycle up to 280C.',
                'priority': 'High',
                'warranty_status': 'Under Warranty',
                'amc_status': 'Active AMC',
                'preferred_visit_date': today + timedelta(days=1),
                'location': 'Jamnagar Petrochem Unit 4',
                'attachments': [],
                'assigned_department': 'Field Service Engineering',
                'assigned_technician_id': 'EMP-003',
                'assigned_technician_name': 'Sanjay Mehta',
                'status': 'Scheduled',
            }
        )

        PreventiveMaintenancePlan.objects.update_or_create(
            id='PM-2026-001',
            defaults={
                'plan_number': 'PM-2026-001',
                'asset_id': 'AST-101',
                'asset_name': 'Messer MultiTherm 4000 CNC Plasma',
                'maintenance_type': 'Preventive Monthly Service & Optical Calibration',
                'frequency': 'Monthly',
                'start_date': today - timedelta(days=15),
                'next_due_date': today + timedelta(days=15),
                'checklist': [
                    {'parameter': 'Torch Height Control (THC) Sensor Voltage', 'expectedValue': '120V +/- 2V', 'passFail': 'Pass'},
                    {'parameter': 'Rack & Pinion Backlash Check', 'expectedValue': '< 0.05 mm', 'passFail': 'Pass'},
                    {'parameter': 'Coolant Filter & De-ionizer Cartridge', 'expectedValue': 'Clear / Clean', 'passFail': 'Pass'},
                ],
                'responsible_technician_id': 'EMP-003',
                'responsible_technician_name': 'Sanjay Mehta',
                'estimated_duration_hours': 3.5,
                'required_spare_parts': [
                    {'itemCode': 'SP-FLT-01', 'itemName': 'Messer Coolant Cartridge', 'qty': 1}
                ],
                'instructions': 'Ensure complete power lock-out tag-out (LOTO) before inspecting drive rails.',
                'status': 'Active'
            }
        )

        BreakdownRecord.objects.update_or_create(
            id='BD-2026-001',
            defaults={
                'breakdown_number': 'BD-2026-001',
                'asset_type': 'Internal Asset',
                'asset_id': 'AST-102',
                'asset_name': 'Davi MCB 4-Roll Plate Bending Machine',
                'serial_number': 'DAVI-IT-77412',
                'breakdown_date': today - timedelta(days=7),
                'breakdown_time': '14:20',
                'reported_by': 'Vikram Rathore',
                'problem': 'Hydraulic auxiliary drop-end cylinder pressure loss during plate release.',
                'severity': 'High',
                'initial_diagnosis': 'O-ring seal extrusion in primary proportional valve block.',
                'assigned_technician_id': 'EMP-003',
                'assigned_technician_name': 'Sanjay Mehta',
                'response_time_minutes': 25,
                'resolution_time_minutes': 180,
                'root_cause': 'Viton O-ring degradation due to hydraulic oil heat above 65C.',
                'corrective_action': 'Replaced seal kit with high-temp Polyurethane Parker kit, tested 250 Bar continuous hold.',
                'spare_parts_used': [
                    {'itemCode': 'SP-SEAL-01', 'itemName': 'Davi Drop-End Seal Kit', 'quantity': 1, 'unitCost': 14500.0}
                ],
                'downtime_hours': 3.5,
                'status': 'Closed',
                'remarks': 'Machine restored to 100% capacity.'
            }
        )

        AMCContract.objects.update_or_create(
            id='AMC-2026-001',
            defaults={
                'amc_number': 'AMC-2026-001',
                'customer_id': 'CUST-001',
                'customer_name': 'Reliance Industries Limited (Jamnagar)',
                'customer_machine_id': 'CM-2026-001',
                'machine_name': 'High Pressure Autoclave Reactor 50 KL',
                'serial_number': 'UMA-RIL-AC-01',
                'contract_start': today - timedelta(days=165),
                'contract_end': today + timedelta(days=200),
                'contract_value': 1250000.0,
                'billing_frequency': 'Quarterly',
                'total_visits_included': 6,
                'visits_completed': 2,
                'preventive_visits': 4,
                'breakdown_support': True,
                'parts_included': False,
                'labour_included': True,
                'response_time_hours': 12,
                'terms_and_conditions': 'Comprehensive on-site technical inspection, emergency callouts within 12 hours.',
                'assigned_technician_id': 'EMP-003',
                'assigned_technician_name': 'Sanjay Mehta',
                'status': 'Active'
            }
        )

        # -------------------------------------------------------------
        # 3. HR & PAYROLL SEEDING
        # -------------------------------------------------------------
        self.stdout.write('  Seeding HR Designations & Shifts...')
        designations = [
            {'id': 'DESIG-01', 'designation_code': 'DESIG-MGT-01', 'designation_name': 'Managing Director & CEO', 'department': 'Executive Management', 'level': 7, 'status': 'Active'},
            {'id': 'DESIG-02', 'designation_code': 'DESIG-ENG-01', 'designation_name': 'Senior Design & Pressure Vessel Engineer', 'department': 'Design Engineering', 'level': 4, 'status': 'Active'},
            {'id': 'DESIG-03', 'designation_code': 'DESIG-PRD-01', 'designation_name': 'Production Plant Superintendent', 'department': 'Production & Works', 'level': 4, 'status': 'Active'},
            {'id': 'DESIG-04', 'designation_code': 'DESIG-QC-01', 'designation_name': 'Lead Quality & NDT Level III Inspector', 'department': 'Quality Assurance', 'level': 3, 'status': 'Active'},
            {'id': 'DESIG-05', 'designation_code': 'DESIG-WLD-01', 'designation_name': 'Certified ASME IX Welder / SAW Specialist', 'department': 'Shop Floor Operations', 'level': 2, 'status': 'Active'},
            {'id': 'DESIG-06', 'designation_code': 'DESIG-HR-01', 'designation_name': 'HR & Payroll Manager', 'department': 'Human Resources', 'level': 3, 'status': 'Active'},
        ]
        for d in designations:
            Designation.objects.update_or_create(id=d['id'], defaults=d)

        shifts = [
            {'id': 'SHF-GEN', 'shift_name': 'General Office & Technical Shift', 'start_time': '09:00', 'end_time': '18:00', 'grace_period_minutes': 15, 'break_duration_minutes': 60, 'weekly_off': 'Sunday', 'status': 'Active'},
            {'id': 'SHF-PRD-A', 'shift_name': 'Plant Production Morning Shift (A)', 'start_time': '07:00', 'end_time': '15:30', 'grace_period_minutes': 10, 'break_duration_minutes': 30, 'weekly_off': 'Sunday', 'status': 'Active'},
            {'id': 'SHF-PRD-B', 'shift_name': 'Plant Production Evening Shift (B)', 'start_time': '15:30', 'end_time': '00:00', 'grace_period_minutes': 10, 'break_duration_minutes': 30, 'weekly_off': 'Sunday', 'status': 'Active'},
        ]
        for s in shifts:
            ShiftMaster.objects.update_or_create(id=s['id'], defaults=s)

        self.stdout.write('  Seeding Salary Components & Structures...')
        sal_components = [
            {'id': 'SC-BSC', 'component_code': 'BASIC', 'component_name': 'Basic Salary', 'component_type': 'Earning', 'calculation_type': 'Fixed Amount', 'is_taxable': True, 'is_statutory': True, 'status': 'Active'},
            {'id': 'SC-HRA', 'component_code': 'HRA', 'component_name': 'House Rent Allowance', 'component_type': 'Earning', 'calculation_type': 'Percentage of Basic', 'percentage_or_formula': '50% of Basic', 'is_taxable': True, 'is_statutory': False, 'status': 'Active'},
            {'id': 'SC-CNV', 'component_code': 'CONV', 'component_name': 'Conveyance Allowance', 'component_type': 'Earning', 'calculation_type': 'Fixed Amount', 'is_taxable': False, 'is_statutory': False, 'status': 'Active'},
            {'id': 'SC-SPL', 'component_code': 'SPL_ALW', 'component_name': 'Special Technical Allowance', 'component_type': 'Earning', 'calculation_type': 'Fixed Amount', 'is_taxable': True, 'is_statutory': False, 'status': 'Active'},
            {'id': 'SC-PF', 'component_code': 'EPF', 'component_name': 'Employee Provident Fund (EPF 12%)', 'component_type': 'Deduction', 'calculation_type': 'Percentage of Basic', 'percentage_or_formula': '12% of Basic', 'is_taxable': False, 'is_statutory': True, 'status': 'Active'},
            {'id': 'SC-PT', 'component_code': 'PT', 'component_name': 'Gujarat Professional Tax', 'component_type': 'Deduction', 'calculation_type': 'Fixed Amount', 'is_taxable': False, 'is_statutory': True, 'status': 'Active'},
        ]
        for sc in sal_components:
            SalaryComponent.objects.update_or_create(id=sc['id'], defaults=sc)

        salary_structures = [
            {
                'id': 'SAL-STR-01',
                'structure_name': 'Senior Technical / Engineering CTC Structure',
                'employee_id': 'EMP-001',
                'employee_name': 'Rajesh Patel',
                'effective_from': date(2026, 4, 1),
                'basic_salary': 45000.0,
                'hra': 22500.0,
                'conveyance_allowance': 5000.0,
                'medical_allowance': 3000.0,
                'special_allowance': 14500.0,
                'gross_salary': 90000.0,
                'employee_pf': 5400.0,
                'employee_esi': 0.0,
                'professional_tax': 200.0,
                'tds_monthly': 6500.0,
                'total_deductions': 12100.0,
                'net_salary': 77900.0,
                'employer_pf': 5400.0,
                'employer_esi': 0.0,
                'total_ctc': 95400.0,
                'status': 'Active'
            },
            {
                'id': 'SAL-STR-02',
                'structure_name': 'Operations Head CTC Structure',
                'employee_id': 'EMP-002',
                'employee_name': 'Vikram Rathore',
                'effective_from': date(2026, 4, 1),
                'basic_salary': 40000.0,
                'hra': 20000.0,
                'conveyance_allowance': 4000.0,
                'medical_allowance': 2500.0,
                'special_allowance': 11500.0,
                'gross_salary': 78000.0,
                'employee_pf': 4800.0,
                'employee_esi': 0.0,
                'professional_tax': 200.0,
                'tds_monthly': 4800.0,
                'total_deductions': 9800.0,
                'net_salary': 68200.0,
                'employer_pf': 4800.0,
                'employer_esi': 0.0,
                'total_ctc': 82800.0,
                'status': 'Active'
            }
        ]
        for ss in salary_structures:
            SalaryStructure.objects.update_or_create(id=ss['id'], defaults=ss)

        self.stdout.write('  Seeding Attendance Records & Leaves...')
        attendance_entries = [
            {'id': 'ATT-2026-001', 'employee_id': 'EMP-001', 'employee_name': 'Rajesh Patel', 'department': 'Design Engineering', 'date': today, 'shift_name': 'General Office & Technical Shift', 'check_in': '08:55', 'check_out': '18:05', 'total_hours': 9.17, 'late_minutes': 0, 'early_checkout_minutes': 0, 'overtime_hours': 0.0, 'status': 'Present', 'source': 'Biometric System'},
            {'id': 'ATT-2026-002', 'employee_id': 'EMP-002', 'employee_name': 'Vikram Rathore', 'department': 'Production & Works', 'date': today, 'shift_name': 'Plant Production Morning Shift (A)', 'check_in': '06:58', 'check_out': '16:00', 'total_hours': 9.03, 'late_minutes': 0, 'early_checkout_minutes': 0, 'overtime_hours': 0.5, 'status': 'Present', 'source': 'Biometric System'},
            {'id': 'ATT-2026-003', 'employee_id': 'EMP-003', 'employee_name': 'Sanjay Mehta', 'department': 'Maintenance', 'date': today, 'shift_name': 'General Office & Technical Shift', 'check_in': '09:02', 'check_out': '18:15', 'total_hours': 9.22, 'late_minutes': 2, 'early_checkout_minutes': 0, 'overtime_hours': 0.25, 'status': 'Present', 'source': 'Biometric System'},
        ]
        for att in attendance_entries:
            AttendanceRecord.objects.update_or_create(id=att['id'], defaults=att)

        LeaveRequest.objects.update_or_create(
            id='LV-2026-101',
            defaults={
                'leave_number': 'LV-2026-101',
                'employee_id': 'EMP-001',
                'employee_name': 'Rajesh Patel',
                'department': 'Design Engineering',
                'leave_type_id': 'LT-CL',
                'leave_name': 'Casual Leave',
                'from_date': today + timedelta(days=10),
                'to_date': today + timedelta(days=11),
                'number_of_days': 2.0,
                'is_half_day': False,
                'reason': 'Family religious function in Ahmedabad.',
                'reporting_manager': 'Managing Director',
                'status': 'Approved',
                'applied_date': today - timedelta(days=2),
                'approved_by': 'Managing Director',
                'approved_date': today - timedelta(days=1),
            }
        )

        self.stdout.write('  Seeding Payroll Records...')
        PayrollRecord.objects.update_or_create(
            id='PAY-2026-AUG-01',
            defaults={
                'payroll_number': 'PAY-2026-AUG-01',
                'month_year': 'August 2026',
                'financial_year': '2026-2027',
                'employee_id': 'EMP-001',
                'employee_name': 'Rajesh Patel',
                'department': 'Design Engineering',
                'designation': 'Senior Design & Pressure Vessel Engineer',
                'working_days': 26.0,
                'present_days': 25.0,
                'leave_days': 1.0,
                'loss_of_pay_days': 0.0,
                'overtime_hours': 4.0,
                'basic_salary': 45000.0,
                'hra': 22500.0,
                'allowances': 22500.0,
                'overtime_amount': 2200.0,
                'gross_earnings': 92200.0,
                'pf_deduction': 5400.0,
                'esi_deduction': 0.0,
                'pt_deduction': 200.0,
                'tds_deduction': 6500.0,
                'loan_advance_recovery': 0.0,
                'other_deductions': 0.0,
                'total_deductions': 12100.0,
                'net_salary': 80100.0,
                'employer_pf': 5400.0,
                'employer_esi': 0.0,
                'total_ctc': 97600.0,
                'status': 'Approved',
                'processed_date': today - timedelta(days=25),
                'approved_by': 'Finance & HR Head',
                'accounting_voucher_ref': 'JV-2026-PAY-AUG-01'
            }
        )

        self.stdout.write(self.style.SUCCESS('[OK] Phase 5 seed completed successfully!'))
