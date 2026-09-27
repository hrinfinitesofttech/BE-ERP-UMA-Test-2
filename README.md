# Uma Techno Fab ERP — Backend (Django REST Framework)

Backend API service for **Uma Techno Fab Private Limited** Make-To-Order Manufacturing ERP.

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- Django 5.2+
- Django REST Framework

### 2. Run Database Migrations & Seed Data
```bash
python manage.py migrate
python manage.py seed_phase1
python manage.py seed_phase2
python manage.py seed_phase3
python manage.py seed_phase4
```

### 3. Start Development Server
```bash
python manage.py runserver 8000
```
Server runs at `http://127.0.0.1:8000/`.

---

## 📡 Available API Endpoints

### 🔐 Phase 1: Authentication & Organization
- `POST /api/auth/login/` — Login with username & password (returns JWT access/refresh tokens and user details)
- `POST /api/auth/token/refresh/` — Refresh access token
- `GET/PATCH /api/auth/me/` — Get or update current logged-in employee profile
- `POST /api/auth/change-password/` — Update password
- `GET/POST /api/employees/` — List / Create employees
- `GET/PUT/DELETE /api/employees/{id}/` — Employee details
- `GET/POST /api/departments/` — List / Create departments
- `GET/POST /api/roles/` — List / Create roles with granular permissions
- `GET/PUT /api/company/` — Company settings & bank details
- `GET/POST /api/numbering/` — Document numbering configurations
- `GET /api/numbering/next-number/?docType=lead` — Preview or generate next sequence number
- `GET/POST /api/audit-logs/` — Immutable audit trail logs
- `GET/POST /api/notifications/` — Real-time notification items

### 💼 Phase 2: CRM & Sales Pipeline
- `GET/POST /api/leads/` — Lead acquisition (with automatic sequence numbering: `LEAD-2026-XXXX`)
- `POST /api/leads/{id}/convert/` — **One-click conversion**: converts lead into Customer, Enquiry & Opportunity
- `GET/POST /api/customers/` — Customer directory with billing/shipping addresses & credit limits
- `GET/POST /api/contacts/` — Customer contacts
- `GET/POST /api/enquiries/` — Technical enquiries (`ENQ-2026-XXXX`)
- `GET/POST /api/opportunities/` — Sales pipeline & win probability tracking (`OPP-2026-XXXX`)
- `GET/POST /api/followups/` — Follow-up logs (Call, Email, WhatsApp, Meeting)
- `POST /api/followups/{id}/complete/` — Complete follow-up with resolution notes
- `GET/POST /api/visits/` — Field site visits with customer discussion notes
- `GET/POST /api/exhibitions/` — Trade expo lead tracking (ENGIMACH, etc.)
- `GET/POST /api/quotations/` — Multi-item commercial quotations with tax/discount calculation
- `POST /api/quotations/{id}/add-revision/` — Append new quotation revision (`Rev-01`, `Rev-02`)
- `POST /api/quotations/{id}/update-status/` — Update revision approval status (`sent`, `accepted`, `rejected`)
- `GET/POST /api/customer-pos/` — Customer PO (CPO) registration
- `POST /api/customer-pos/{id}/convert-to-so/` — **Convert CPO into Sales Order** (`SO-2026-XXXX`)
- `GET/POST /api/sales-orders/` — Confirmed Sales Orders ready for Project Management handover
- `GET/POST /api/activities/` — CRM activity timeline

### ⚙️ Phase 3: Project Management & Design Engineering (Pre-Production)
- `GET/POST /api/projects/` — Make-to-Order Projects (`PRJ-2026-XXXX` / `JOB-2026-XXXX`). **Auto-generates the 16 Standard Planning Stages on project creation!**
- `POST /api/projects/{id}/generate-stages/` — Re-generate or initialize 16 Planning Stages
- `GET/POST /api/planning-stages/` — Planning Stages filterable by `?projectId=PRJ-2026-XXXX`
- `POST /api/planning-stages/{id}/complete/` — Mark a planning stage complete with completion notes
- `GET/POST /api/project-milestones/` — Project payment & production milestones
- `GET/POST /api/project-tasks/` — Departmental project tasks & assignments
- `GET/POST /api/project-issues/` — Project bottlenecks, quality issues & resolution tracking
- `GET/POST /api/project-costs/` — Estimated vs Actual cost tracking per category (material, labor, machining)
- `GET/POST /api/design-jobs/` — Design Engineering Jobs (`DES-2026-XXXX`)
- `POST /api/design-jobs/{id}/release-to-production/` — **Officially releases Design & BOM to Production**
- `GET/POST /api/design-requirements/` — Customer technical & machine specifications
- `GET/POST /api/drawings-2d/` — 2D CAD General Arrangement (GA) & fabrication drawings
- `GET/POST /api/models-3d/` — 3D SolidWorks assembly models & mass properties
- `GET/POST /api/boms/` — Multi-level Bill of Materials (BOM) with items & procurement types
- `POST /api/boms/{id}/add-item/` — Append new raw material or bought-out component to BOM

### 📦 Phase 4: Procurement, Store & Inventory Management
- `GET/POST /api/suppliers/` — Supplier/Vendor master with ratings & payment terms
- `GET/POST /api/purchase-requisitions/` — Indent & Purchase Requisitions (`PR-2026-XXXX`)
- `POST /api/purchase-requisitions/{id}/convert-to-rfq/` — **Convert PR into RFQ**
- `GET/POST /api/rfqs/` — Request For Quotation (`RFQ-2026-XXXX`)
- `GET/POST /api/supplier-quotations/` — Vendor quotations & comparative analysis
- `GET/POST /api/purchase-orders/` — Purchase Orders (`PO-2026-XXXX`)
- `POST /api/purchase-orders/{id}/approve/` — Approve Purchase Order
- `GET/POST /api/purchase-returns/` — Purchase returns & debit notes
- `GET/POST /api/items/` — Raw Material, Bought-out, Consumable Item Master with HSN/GST
- `GET/POST /api/item-categories/` — Item Categories
- `GET/POST /api/uoms/` — Unit of Measurement master
- `GET/POST /api/warehouses/` — Warehouses & bay locations
- `GET/POST /api/grns/` — **Goods Receipt Note (GRN)**: automatically updates stock balances and ledger
- `GET/POST /api/qc-inspections/` — Inward Quality Control inspections (Pass, Fail, Conditional)
- `GET/POST /api/stock/` — Real-time Stock Balances (Total, Reserved, Available)
- `GET/POST /api/material-issues/` — Issue material to shopfloor jobs (automatically deducts stock and logs ledger)
- `GET/POST /api/material-returns/` — Return unused material from shop floor back to store
- `GET/POST /api/stock-ledger/` — Perpetual Stock Ledger entries (inward, outward, balance)
- `GET/POST /api/scrap/` — Scrap identification & disposal logs

### Phase 5: Production Execution, Plant Maintenance & Services, HR & Payroll
- `GET/POST /api/manufacturing-jobs/` — Manufacturing Jobs with 1-to-1 Project linking
  - `POST /api/manufacturing-jobs/{id}/update-progress/` — Update shopfloor execution progress
- `GET/POST /api/production-plans/` — Production Planning with material availability check
- `GET/POST /api/work-centers/` — Machine & Bay Work Centers (Plasma, Rolling, SAW, Boring, Testing)
- `GET/POST /api/routing-operations/` — Sequential operations, standard times, and operators
- `GET/POST /api/work-orders/` — Shop floor work orders
  - `POST /api/work-orders/{id}/release/` — Release work order to shopfloor
- `GET/POST /api/production-orders/` — Production orders
- `GET/POST /api/production-schedules/` — Machine schedule tracking
- `GET/POST /api/production-entries/` — Daily shift logs, good/rejected/scrap quantities
- `GET/POST /api/wip-records/` — Real-time WIP location & stage tracking
- `GET/POST /api/production-holds/` — Active production holds
  - `POST /api/production-holds/{id}/resume/` — Resume production hold
- `GET/POST /api/rework-orders/` — Non-conformance rework tracking
- `GET/POST /api/production-scraps/` — Fabrication scrap entries
- `GET/POST /api/finished-goods/` — Finished equipment stock
  - `POST /api/finished-goods/{id}/qc-pass/` — Pass final QC inspection
- `GET/POST /api/internal-assets/` — Heavy machinery assets, warranty & PM cycles
- `GET/POST /api/customer-machines/` — Commissioned customer equipment registry
- `GET/POST /api/service-requests/` — Customer service complaints & tickets
  - `POST /api/service-requests/{id}/assign/` — Assign field technician
  - `POST /api/service-requests/{id}/resolve/` — Resolve service request
- `GET/POST /api/pm-plans/` — Preventive Maintenance schedules & digital checklists
- `GET/POST /api/breakdowns/` — Unscheduled machine breakdowns & root cause analysis
- `GET/POST /api/service-visits/` — On-site technician service visit reports
- `GET/POST /api/amc-contracts/` — Annual Maintenance Contracts & visit quotas
- `GET/POST /api/designations/` — Organizational designations & grade levels
- `GET/POST /api/employee-documents/` — Document compliance (Aadhaar, PAN, certificates)
- `GET/POST /api/shifts/` — Factory shift masters & timings
- `GET/POST /api/attendance-records/` — Biometric daily attendance logs
- `GET/POST /api/leave-requests/` — Leave applications & approval workflows
- `GET/POST /api/wfh-requests/` — WFH requests
- `GET/POST /api/missed-punches/` — Attendance regularizations & missed punch requests
- `GET/POST /api/overtime-records/` — Overtime calculation & approval
- `GET/POST /api/salary-components/` — Statutory earnings & deductions (PF, ESI, PT, TDS)
- `GET/POST /api/salary-structures/` — Employee CTC breakdown structures
- `GET/POST /api/payroll-records/` — Monthly payroll generation & approval
  - `POST /api/payroll-records/generate-monthly-payroll/` — Auto-calculate monthly payroll

### Phase 6: Accounting, Finance, 360° Job Traceability & Central Approvals
- `GET/POST /api/financial-years/` — Financial Years with Active/Closed states
- `GET/POST /api/chart-of-accounts/` — Full Chart of Accounts (Assets, Liabilities, Income, Expenses)
- `GET/POST /api/taxes/` — GST Tax Masters (CGST, SGST, IGST) with HSN/SAC codes
- `GET/POST /api/cost-centers/` — Cost Centers across fabrication, design, and site services
- `GET/POST /api/sales-invoices/` — Tax Invoices with item breakdowns, GST, and auto-balancing
  - `POST /api/sales-invoices/{id}/record-payment/` — Record customer payment, update outstanding, and auto-create receipt
  - `POST /api/sales-invoices/{id}/post/` — Post invoice to ledger
- `GET/POST /api/purchase-invoices/` — Vendor bills linked to Purchase Orders & GRNs
  - `POST /api/purchase-invoices/{id}/record-payment/` — Record supplier payment and auto-create payment entry
- `GET/POST /api/customer-receipts/` — Customer payment receipts (RTGS, NEFT, Cheque)
- `GET/POST /api/supplier-payments/` — Supplier payment disbursement logs
- `GET/POST /api/journal-entries/` — Multi-line double entry journal vouchers
- `GET/POST /api/job-costings/` — Real-time job profitability summaries (Actual vs Estimated margins)
- `GET/POST /api/approvals/` — Central Approval Center queue across all modules
  - `POST /api/approvals/{id}/approve/` — Approve document
  - `POST /api/approvals/{id}/reject/` — Reject document
- `GET/POST /api/alerts/` — System alerts & operational notifications
  - `POST /api/alerts/{id}/mark-read/` — Mark alert as read
- `GET /api/job-360/<job_number>/` — **360° Job Traceability Master API**: returns the complete end-to-end trace connecting CRM, Engineering, BOM, Purchase Orders, Store Stock, Production, QC, Dispatch, Invoicing, and Field Maintenance!

---

## 🔑 Key Naming Convention
All APIs automatically serialize and deserialize JSON with **camelCase** keys to match the frontend TypeScript types in `FE-ERP-UMA` 1-to-1.


