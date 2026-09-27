from django.core.management.base import BaseCommand
from apps.projects.models import (
    ProjectJobMaster,
    ProjectMilestone,
    ProjectTask,
    DepartmentAssignment,
    ProjectIssue,
    ProjectDelay,
    ProjectCost,
)
from apps.projects.views import auto_generate_16_stages
from apps.designer.models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    BOMHeader,
)


class Command(BaseCommand):
    help = 'Seeds initial Project Management and Design Engineering data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Phase 3 Project & Design Data Seeding...'))

        # 1. Project Job Master
        project, _ = ProjectJobMaster.objects.update_or_create(
            id='PRJ-2026-0042',
            defaults={
                'project_number': 'PRJ-2026-0042',
                'job_number': 'JOB-2026-0042',
                'customer_id': 'CUST-2026-0001',
                'customer_name': 'Gujarat Alkalies & Chemicals Ltd.',
                'sales_order_id': 'SO-2026-0042',
                'sales_order_number': 'SO-2026-0042',
                'customer_po_number': 'PO/GACL/FAB/2026/089',
                'product_name': 'Heavy SS 316L Chemical Reactor Vessel (10 KL)',
                'product_code': 'EQ-CRV-10K',
                'specification': '10,000 Litres Limpet Jacketed SS 316L Chemical Reactor, 8 Bar Design Pressure, ASME Sec VIII Div 1',
                'quantity': 1,
                'unit': 'Set',
                'order_value': 4850000,
                'start_date': '2026-08-10',
                'target_delivery_date': '2026-10-15',
                'current_status': 'production',
                'progress_percent': 42,
                'priority': 'high',
                'project_manager_id': 'EMP-004',
                'project_manager_name': 'Bhavin Shah',
                'stage': 'Fabrication & Welding',
                'health_status': 'on_track',
                'linked_records': {
                    'leadId': 'LEAD-2026-0101',
                    'quotationId': 'QT-2026-0118',
                    'salesOrderId': 'SO-2026-0042',
                    'designJobId': 'DES-2026-0001',
                    'bomId': 'BOM-CRV-10K',
                },
            }
        )
        self.stdout.write(self.style.SUCCESS(f'[OK] Project {project.project_number} seeded.'))

        # 2. 16 Standard Planning Stages
        stages = auto_generate_16_stages(project.id)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(stages)} Planning stages generated for {project.id}.'))

        # 3. Project Milestones
        milestones_data = [
            {'id': 'mls-1', 'project_id': project.id, 'title': 'Advance Payment & Kickoff', 'milestone_code': 'M1', 'target_date': '2026-08-10', 'completion_date': '2026-08-10', 'status': 'completed', 'payment_percentage': 30, 'payment_amount': 1455000, 'department': 'CRM'},
            {'id': 'mls-2', 'project_id': project.id, 'title': 'GA Drawing & Engineering Sign-off', 'milestone_code': 'M2', 'target_date': '2026-08-25', 'completion_date': '2026-08-24', 'status': 'completed', 'payment_percentage': 0, 'payment_amount': 0, 'department': 'Design'},
            {'id': 'mls-3', 'project_id': project.id, 'title': 'Shell Plate Rolling & Long-Seam Fitup', 'milestone_code': 'M3', 'target_date': '2026-09-20', 'completion_date': '2026-09-18', 'status': 'completed', 'payment_percentage': 0, 'payment_amount': 0, 'department': 'Production'},
            {'id': 'mls-4', 'project_id': project.id, 'title': 'Hydrostatic Pressure Testing (12.5 Bar)', 'milestone_code': 'M4', 'target_date': '2026-10-05', 'status': 'pending', 'payment_percentage': 0, 'payment_amount': 0, 'department': 'Quality'},
            {'id': 'mls-5', 'project_id': project.id, 'title': 'Final Inspection & Dispatch Clearance', 'milestone_code': 'M5', 'target_date': '2026-10-15', 'status': 'pending', 'payment_percentage': 60, 'payment_amount': 2910000, 'department': 'Dispatch'},
        ]
        for m in milestones_data:
            ProjectMilestone.objects.update_or_create(id=m['id'], defaults=m)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(milestones_data)} Milestones seeded.'))

        # 4. Project Tasks
        tasks_data = [
            {'id': 'tsk-1', 'project_id': project.id, 'task_number': 'TSK-001', 'title': '3D CAD Model & Nozzle Table Finalization', 'department': 'designer', 'assigned_to_name': 'Dharmesh Joshi', 'status': 'completed', 'priority': 'high', 'due_date': '2026-08-20'},
            {'id': 'tsk-2', 'project_id': project.id, 'task_number': 'TSK-002', 'title': 'SS 316L Plates (8mm & 10mm) Inward Inspection', 'department': 'store', 'assigned_to_name': 'Hitesh Rawal', 'status': 'completed', 'priority': 'urgent', 'due_date': '2026-09-05'},
            {'id': 'tsk-3', 'project_id': project.id, 'task_number': 'TSK-003', 'title': 'SAW Welding of Shell Longitudinal Joints', 'department': 'production', 'assigned_to_name': 'Bhavin Shah', 'status': 'in_progress', 'priority': 'high', 'due_date': '2026-09-25'},
        ]
        for t in tasks_data:
            ProjectTask.objects.update_or_create(id=t['id'], defaults=t)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(tasks_data)} Tasks seeded.'))

        # 5. Design Job
        design_job, _ = DesignJob.objects.update_or_create(
            id='DES-2026-0001',
            defaults={
                'design_job_number': 'DES-2026-0001',
                'project_id': project.id,
                'project_number': project.project_number,
                'job_number': project.job_number,
                'customer_id': project.customer_id,
                'customer_name': project.customer_name,
                'customer_po_number': project.customer_po_number,
                'sales_order_number': project.sales_order_number,
                'product_name': project.product_name,
                'machine_type': 'Chemical Reactor Pressure Vessel',
                'quantity': 1,
                'delivery_date': project.target_delivery_date,
                'design_manager': 'Dharmesh Joshi',
                'assigned_designer': 'Ketan Patel',
                'priority': 'high',
                'status': 'bom_approved',
                'active_revision': 'REV-02',
                'created_date': '2026-08-11',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'[OK] Design Job {design_job.design_job_number} seeded.'))

        # 6. Customer Technical Requirement
        CustomerRequirement.objects.update_or_create(
            id='REQ-2026-001',
            defaults={
                'design_job_id': design_job.id,
                'project_id': project.id,
                'job_number': project.job_number,
                'customer_name': project.customer_name,
                'contact_person': 'Harish Trivedi',
                'contact_mobile': '+91 98251 99881',
                'machine_name': 'Heavy SS 316L Chemical Reactor Vessel (10 KL)',
                'machine_type': 'Vertical Jacketed Reactor',
                'model': 'UTF-CRV-10000',
                'quantity': 1,
                'capacity': '10,000 Litres Working Volume',
                'application': 'Corrosive Acid Formulation with Anchor Agitator',
                'dimensions': 'Shell Dia 2000mm x Height 3500mm',
                'material': 'Contact parts: SS 316L, Jacket: SS 304',
                'power_requirement': '15 HP Flameproof IE3 Motor with Helical Gearbox',
                'speed': '45 RPM (VFD controlled)',
                'control_system': 'Flameproof Local Control Station + SCADA interface',
                'safety_requirements': 'Dual Safety Relief Valves, Rupture Disc, Nitrogen Purging Interlock',
                'customer_notes': 'Full radiography on shell weld joints required. FAT inspection by GACL inspection engineer.',
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Customer Technical Requirement seeded.'))

        # 7. 2D Drawing & 3D Model
        Drawing2D.objects.update_or_create(
            id='DWG-2026-001',
            defaults={
                'design_job_id': design_job.id,
                'drawing_number': 'UTF-CRV-10K-GA-001',
                'title': 'General Arrangement (GA) Drawing & Nozzle Table',
                'revision': 'REV-02',
                'status': 'approved',
                'scale': '1:10',
                'sheet_size': 'A0',
                'prepared_by': 'Ketan Patel',
                'checked_by': 'Dharmesh Joshi',
                'approved_by': 'Rajesh Patel',
                'release_date': '2026-08-24',
                'file_url': '/drawings/UTF-CRV-10K-GA-001-R2.pdf',
            }
        )

        Design3DModel.objects.update_or_create(
            id='MOD-2026-001',
            defaults={
                'design_job_id': design_job.id,
                'model_number': '3D-CRV-10K-ASM',
                'model_name': 'Full 3D CAD Assembly of 10 KL Reactor with Drive',
                'software': 'SolidWorks',
                'version': '2026 SP1',
                'status': 'approved',
                'mass_kg': 6450,
                'volume_m3': 12.8,
                'modeled_by': 'Ketan Patel',
                'file_url': '/models/3D-CRV-10K-ASM.STEP',
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] 2D Drawing & 3D Model seeded.'))

        # 8. BOM Header with multi-level exploded items
        bom_items = [
            {'itemCode': 'RM-SS316L-PL-8MM', 'itemName': 'SS 316L Plates (8mm thk, SA 240)', 'itemType': 'Raw Material', 'classification': 'purchased', 'materialGrade': 'SS 316L', 'quantity': 1850, 'unit': 'Kg', 'procurementType': 'Purchase', 'estimatedRate': 345, 'totalEstimatedAmount': 638250},
            {'itemCode': 'RM-SS316L-DISH-10MM', 'itemName': 'Torispherical Dish Ends (Dia 2000mm, 10mm thk)', 'itemType': 'Fabricated', 'classification': 'manufactured', 'materialGrade': 'SS 316L', 'quantity': 2, 'unit': 'Nos', 'procurementType': 'Fabricate', 'estimatedRate': 185000, 'totalEstimatedAmount': 370000},
            {'itemCode': 'BO-MTR-15HP-FLP', 'itemName': 'ABB 15 HP Flameproof Electric Motor (IE3, 1440 RPM)', 'itemType': 'Bought-Out', 'classification': 'standard', 'materialGrade': 'Cast Iron / FLP Ex-d', 'quantity': 1, 'unit': 'Nos', 'procurementType': 'Purchase', 'estimatedRate': 145000, 'totalEstimatedAmount': 145000},
            {'itemCode': 'BO-SEAL-DUAL-75MM', 'itemName': 'Burgmann Dual Mechanical Seal with Thermosiphon Pot', 'itemType': 'Bought-Out', 'classification': 'standard', 'materialGrade': 'Hastelloy C / SiC Faces', 'quantity': 1, 'unit': 'Set', 'procurementType': 'Purchase', 'estimatedRate': 285000, 'totalEstimatedAmount': 285000},
            {'itemCode': 'RM-PIPE-SS304-LIMPET', 'itemName': 'SS 304 Half Pipe Limpet Coil (75mm NB)', 'itemType': 'Raw Material', 'classification': 'purchased', 'materialGrade': 'SS 304', 'quantity': 140, 'unit': 'Mtr', 'procurementType': 'Purchase', 'estimatedRate': 1200, 'totalEstimatedAmount': 168000},
        ]
        BOMHeader.objects.update_or_create(
            id='BOM-CRV-10K',
            defaults={
                'bom_number': 'BOM-CRV-10K',
                'design_job_id': design_job.id,
                'project_id': project.id,
                'job_number': project.job_number,
                'active_revision': 'REV-02',
                'status': 'approved',
                'total_items': len(bom_items),
                'total_weight_kg': 6450,
                'total_estimated_cost': 1606250,
                'prepared_by': 'Ketan Patel',
                'approved_by': 'Dharmesh Joshi',
                'release_date': '2026-08-28',
                'items': bom_items,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'[OK] BOM Header BOM-CRV-10K with {len(bom_items)} items seeded.'))
        self.stdout.write(self.style.SUCCESS('Done: Phase 3 Project & Design Seeding Complete!'))
