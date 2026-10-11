# UmaERP — Safe Client Go-Live Database Cleanup & Model Inventory Report

**Date & Time:** October 11, 2026  
**System:** Uma Techno Fab ERP (Django 4.2.30 / Python 3.10 & 3.11)  
**Status:** **INVENTORY & DRY-RUN COMPLETED — PENDING CLIENT / USER APPROVAL**  
**Execution State:** Zero destructive changes applied to live production or local databases.

---

## 1. Executive Summary & Safety Compliance

Before handing UmaERP to the client, an end-to-end database audit, verified backup, and dry-run cleanup simulation were executed.

* **Database Isolation Verified:** The deployed production database hosted on PythonAnywhere and the local development database were proven to be separate instances with different row counts and file sizes.
* **Verified Database Backups Created:** Full binary backups of both the remote production database and local database were created and verified with SQLite `PRAGMA integrity_check` returning `ok`.
* **Complete Model Inventory:** All 151 Django models across 13 applications (including unregistered admin models and Django internals) were mapped and counted.
* **Testing Transaction Scope Identified:** **2,519 test business transaction records** across 68 transaction models in the live production database are slated for reset.
* **System & Master Protection Enforced:** Superusers, staff accounts, company configuration, numbering series, chart of accounts, tax slabs, item categories, UOMs, warehouses, work centers, and HR designations are **100% preserved**.
* **Dry-Run Validated:** The custom management command `cleanup_testing_data` was implemented, tested, and validated in an isolated sandbox clone with zero foreign key violations and 100% clean post-cleanup verification.

---

## 2. Target Database Identification

| Parameter | Live Production Deployment (PythonAnywhere) | Local Development Environment |
| :--- | :--- | :--- |
| **Hosting Platform** | PythonAnywhere (`umaERP.pythonanywhere.com`) | Local Windows Workstation (`d:\UMA ERP\BE-ERP-UMA`) |
| **API Health Domain** | `https://erpuma.pythonanywhere.com/api/health/` | `http://127.0.0.1:8000/api/health/` |
| **Configured Engine** | `django.db.backends.sqlite3` | `django.db.backends.sqlite3` |
| **Active DB File Path** | `/home/umaERP/BE-ERP-UMA/db.sqlite3` | `d:\UMA ERP\BE-ERP-UMA\db.sqlite3` |
| **Active File Size** | **3,014,656 bytes (~3.01 MB)** | **2,191,360 bytes (~2.19 MB)** |
| **Table Count** | 154 tables | 156 tables (includes 2 newly migrated local tables) |
| **Transaction Rows** | **2,519 rows** | **434 rows** |

> [!IMPORTANT]
> **Safety Finding:** As required by Rule #1, the production database on PythonAnywhere was explicitly inspected and downloaded rather than assuming the local database is production. All production cleanup commands must target `/home/umaERP/BE-ERP-UMA/db.sqlite3`.

---

## 3. Verified Pre-Reset Database Backups

Two pre-reset backups have been created and byte-verified on disk:

1. **Production Database Verified Backup:**
   * **Local Backup Path:** `d:\UMA ERP\BE-ERP-UMA\backups\pythonanywhere_live_db_backup_pre_reset_20261010.sqlite3`
   * **Source:** Downloaded directly from PythonAnywhere `/home/umaERP/BE-ERP-UMA/db.sqlite3` via Authenticated API.
   * **Size:** `3,014,656 bytes`
   * **Integrity Status:** `PRAGMA integrity_check;` -> `[('ok',)]`
   * **Preservation Status:** Permanently stored in `backups/`.

2. **Local Development Database Verified Backup:**
   * **Local Backup Path:** `d:\UMA ERP\BE-ERP-UMA\backups\db_backup_pre_reset_20261010_231830.sqlite3`
   * **Size:** `2,191,360 bytes`
   * **Integrity Status:** `PRAGMA integrity_check;` -> `[('ok',)]`
   * **Preservation Status:** Permanently stored in `backups/`.

---

## 4. Comprehensive Model Inventory & Classification

Across all 13 Django applications, models are classified into 4 strict categories:

### Category A: Strictly Preserved (System / Auth / Security / Schema)
*Never deleted under any circumstances.*

| App & Model Identifier | Database Table | Prod Rows | Local Rows | Preservation Rationale |
| :--- | :--- | :---: | :---: | :--- |
| `authentication.User` | `authentication_user` | 6 | 6 | Superuser (`rajesh.admin`, `admin`), executive logins |
| `auth.Group` | `auth_group` | 0 | 0 | Django security groups |
| `auth.Permission` | `auth_permission` | 604 | 604 | Django security permissions |
| `contenttypes.ContentType` | `django_content_type` | 151 | 151 | Django model schema content types |
| `admin.LogEntry` | `django_admin_log` | 7 | 1 | Admin actions audit log |
| `sessions.Session` | `django_session` | 9 | 2 | Active user web sessions |
| `core.CompanySetting` | `core_companysetting` | 1 | 1 | Uma Techno Fab Pvt Ltd legal profile & GSTIN |
| `core.NumberingSetting` | `core_numberingsetting` | 9 | 9 | Document prefix formats (LEAD-, QT-, PO-, etc.) |
| *Schema Migrations* | `django_migrations` | 60 | 71 | Django migration state integrity |
| **Category A Total** | | **777** | **773** | **STRICTLY PRESERVED** |

### Category B: Operational Masters & Reference Data
*Required for ongoing application operation and ERP workflows. Preserved.*

| App & Model Identifier | Database Table | Prod Rows | Local Rows | Master Description |
| :--- | :--- | :---: | :---: | :--- |
| `organization.Department` | `organization_department` | 9 | 9 | Departments (CRM, PRJ, DES, PUR, PROD, QC, etc.) |
| `organization.Role` | `organization_role` | 4 | 4 | Roles (Super Admin, Dept Head, Executive, Auditor) |
| `accounting.FinancialYear` | `accounting_financialyear` | 2 | 2 | FY 2025-26, FY 2026-27 |
| `accounting.ChartOfAccount` | `accounting_chartofaccount` | 11 | 11 | Standard Chart of Accounts (Assets, Liabilities, etc.) |
| `accounting.TaxMaster` | `accounting_taxmaster` | 3 | 3 | GST 18%, GST 12%, GST 28% combinations |
| `accounting.CostCenter` | `accounting_costcenter` | 3 | 3 | Production, Engineering, Maintenance cost centers |
| `accounting.BankAccount` | `accounting_bankaccount` | 4 | 4 | Company bank accounts |
| `store.ItemCategory` | `store_itemcategory` | 4 | 4 | Raw Material, Bought-Out, Consumable, FG |
| `store.UOMMaster` | `store_uommaster` | 4 | 4 | Kg, Nos, Meter, Set |
| `store.Warehouse` | `store_warehouse` | 2 | 2 | Main Store, Yard |
| `store.WarehouseLocation` | `store_warehouselocation` | 0 | 0 | Sub-locations |
| `production.WorkCenter` | `production_workcenter` | 6 | 5 | Plasma Cutting Bay, 4-Roll Bending, Welding Bay |
| `production.RoutingOperation` | `production_routingoperation` | 7 | 5 | Standard machining & fabrication operations |
| `hr.Designation` | `hr_designation` | 6 | 6 | Managing Director, Sales Executive, Design Eng. |
| `hr.ShiftMaster` | `hr_shiftmaster` | 3 | 3 | General Shift, Night Shift, Morning Shift |
| `hr.Holiday` | `hr_holiday` | 16 | 16 | 2026 Statutory Holiday Calendar |
| `hr.SalaryComponent` | `hr_salarycomponent` | 6 | 6 | Basic, HRA, Medical, PF, ESI components |
| `maintenance.InternalAsset` | `maintenance_internalasset` | 3 | 3 | Plant machinery (Messer CNC Plasma, Davi Roll) |
| `maintenance.CustomerMachine` | `maintenance_customermachine` | 4 | 4 | Customer installed machinery register |
| **Category B Total** | | **97** | **94** | **PRESERVED** |

---

### Category C: Entity Masters (Preserved by Default; Explicit Approval Required for Reset)
*Master records created during testing. Retained unless client explicitly requests blank lists.*

| App & Model Identifier | Database Table | Prod Rows | Local Rows | Ambiguous / Test Records Detected |
| :--- | :--- | :---: | :---: | :--- |
| `crm.Customer` | `crm_customer` | 58 | 18 | 16 test customers (e.g. `Audit Petrochem Ltd`, `test 1 Aluminium`, `E2E Manufacturing`) |
| `crm.Contact` | `crm_contact` | 1 | 0 | Linked customer contact |
| `crm.Exhibition` | `crm_exhibition` | 2 | 2 | Trade shows (ENGIMACH 2026) |
| `purchase.Supplier` | `purchase_supplier` | 5 | 4 | Jindal Stainless, ABB India, Ratnamani Metals |
| `purchase.SupplierContact` | `purchase_suppliercontact` | 1 | 0 | Supplier representative |
| `store.ItemMaster` | `store_itemmaster` | 20 | 6 | 2 test items (`QA-STOCK-9234`, `ITM-01: Test Item`) |
| **Category C Total** | | **87** | **30** | **PRESERVED (Wiped only if approved)** |

---

### Category D: Testing Business Transactions (Approved Go-Live Cleanup Candidates)
*All transactional records proposed for reset. Ordered topologically by foreign-key / logical dependency.*

| Module | Model Identifier | Database Table | Prod Rows | Local Rows | Action in Dry-Run |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Integration** | `integration.ApprovalItem` | `integration_approvalitem` | 4 | 4 | **DELETE** |
| | `integration.ERPAlertItem` | `integration_erpalertitem` | 4 | 4 | **DELETE** |
| | `integration.GlobalActivityLog` | `integration_globalactivitylog` | 0 | 0 | Clean |
| | `integration.JobProfitabilityRecord`| `integration_jobprofitabilityrecord`| 0 | 0 | Clean |
| **Core** | `core.Notification` | `core_notification` | 479 | 0 | **DELETE** |
| **Accounting** | `accounting.ContraVoucher` | `accounting_contravoucher` | 1 | 1 | **DELETE** |
| | `accounting.ExpenseEntry` | `accounting_expenseentry` | 0 | 0 | Clean |
| | `accounting.DebitNote` | `accounting_debitnote` | 0 | 0 | Clean |
| | `accounting.CreditNote` | `accounting_creditnote` | 0 | 0 | Clean |
| | `accounting.JobCostingSummary` | `accounting_jobcostingsummary` | 2 | 2 | **DELETE** |
| | `accounting.JournalEntry` | `accounting_journalentry` | 1 | 1 | **DELETE** |
| | `accounting.SupplierPayment` | `accounting_supplierpayment` | 5 | 1 | **DELETE** |
| | `accounting.CustomerReceipt` | `accounting_customerreceipt` | 21 | 16 | **DELETE** |
| | `accounting.PurchaseInvoice` | `accounting_purchaseinvoice` | 2 | 1 | **DELETE** |
| | `accounting.SalesInvoice` | `accounting_salesinvoice` | 12 | 5 | **DELETE** |
| **Maintenance**| `maintenance.DowntimeRecord` | `maintenance_downtimerecord` | 0 | 0 | Clean |
| | `maintenance.WarrantyRecord` | `maintenance_warrantyrecord` | 0 | 0 | Clean |
| | `maintenance.ServiceReport` | `maintenance_servicereport` | 0 | 0 | Clean |
| | `maintenance.ServicePartReturn`| `maintenance_servicepartreturn`| 0 | 0 | Clean |
| | `maintenance.ServicePartIssue` | `maintenance_servicepartissue` | 0 | 0 | Clean |
| | `maintenance.ServiceWorkOrder` | `maintenance_serviceworkorder` | 0 | 0 | Clean |
| | `maintenance.ServiceVisit` | `maintenance_servicevisit` | 2 | 0 | **DELETE** |
| | `maintenance.BreakdownRecord` | `maintenance_breakdownrecord` | 1 | 1 | **DELETE** |
| | `maintenance.ServiceRequest` | `maintenance_servicerequest` | 1 | 1 | **DELETE** |
| | `maintenance.PreventiveMaintenancePlan` | `maintenance_preventivemaintenanceplan` | 1 | 1 | **DELETE** |
| | `maintenance.AMCContract` | `maintenance_amccontract` | 1 | 1 | **DELETE** |
| **HR Operations**| `hr.EarlyCheckoutRequest` | `hr_earlycheckoutrequest` | 0 | 0 | Clean |
| | `hr.OvertimeRecord` | `hr_overtimerecord` | 0 | 0 | Clean |
| | `hr.MissedPunchRequest` | `hr_missedpunchrequest` | 0 | 0 | Clean |
| | `hr.AttendanceRegularization` | `hr_attendanceregularization` | 0 | 0 | Clean |
| | `hr.WFHRequest` | `hr_wfhrequest` | 0 | 0 | Clean |
| | `hr.LeaveRequest` | `hr_leaverequest` | 1 | 1 | **DELETE** |
| | `hr.AttendanceRecord` | `hr_attendancerecord` | 3 | 3 | **DELETE** |
| | `hr.PayrollRecord` | `hr_payrollrecord` | 3 | 3 | **DELETE** |
| | `hr.EmployeeAdvanceLoan` | `hr_employeeadvanceloan` | 0 | 0 | Clean |
| | `hr.ReimbursementExpense` | `hr_reimbursementexpense` | 0 | 0 | Clean |
| | `hr.EmployeeAppraisal` | `hr_employeeappraisal` | 0 | 0 | Clean |
| | `hr.EmployeeExit` | `hr_employeeexit` | 0 | 0 | Clean |
| | `hr.EmployeePromotion` | `hr_employeepromotion` | 0 | 0 | Clean |
| | `hr.EmployeeTransfer` | `hr_employeetransfer` | 0 | 0 | Clean |
| | `hr.EmployeeOnboarding` | `hr_employeeonboarding` | 1 | 1 | **DELETE** |
| | `hr.EmployeeDocument` | `hr_employeedocument` | 0 | 0 | Clean |
| | `hr.SalaryStructure` | `hr_salarystructure` | 2 | 2 | **DELETE** |
| **Production** | `production.ProductionCompletion`| `production_productioncompletion`| 0 | 0 | Clean |
| | `production.PackingOrder` | `production_packingorder` | 0 | 0 | Clean |
| | `production.DispatchOrder` | `production_dispatchorder` | 12 | 5 | **DELETE** |
| | `production.FinishedGoodsItem` | `production_finishedgoodsitem` | 39 | 6 | **DELETE** |
| | `production.ProductionScrap` | `production_productionscrap` | 2 | 0 | **DELETE** |
| | `production.ReworkOrder` | `production_reworkorder` | 2 | 0 | **DELETE** |
| | `production.ProductionHold` | `production_productionhold` | 2 | 0 | **DELETE** |
| | `production.WIPRecord` | `production_wiprecord` | 1 | 1 | **DELETE** |
| | `production.ProductionEntry` | `production_productionentry` | 5 | 6 | **DELETE** |
| | `production.ProductionScheduleItem`| `production_productionscheduleitem`| 6 | 0 | **DELETE** |
| | `production.ProductionOrder` | `production_productionorder` | 5 | 1 | **DELETE** |
| | `production.WorkOrder` | `production_workorder` | 67 | 28 | **DELETE** |
| | `production.ProductionPlan` | `production_productionplan` | 6 | 0 | **DELETE** |
| | `production.ProductionMaterialRequest`| `production_productionmaterialrequest`| 7 | 0 | **DELETE** |
| | `production.ManufacturingJob` | `production_manufacturingjob` | 3 | 3 | **DELETE** |
| **Store & Stock**| `store.ScrapEntry` | `store_scrapentry` | 0 | 0 | Clean |
| | `store.StockAdjustment` | `store_stockadjustment` | 0 | 0 | Clean |
| | `store.StockTransfer` | `store_stocktransfer` | 0 | 0 | Clean |
| | `store.MaterialReturn` | `store_materialreturn` | 1 | 0 | **DELETE** |
| | `store.MaterialIssue` | `store_materialissue` | 24 | 12 | **DELETE** |
| | `store.StockReservation` | `store_stockreservation` | 0 | 0 | Clean |
| | `store.StockLedgerEntry` | `store_stockledgerentry` | 80 | 28 | **DELETE** |
| | `store.StockBalance` | `store_stockbalance` | 17 | 3 | **RESET TO ZERO** |
| | `store.QCInspection` | `store_qcinspection` | 34 | 1 | **DELETE** |
| | `store.GoodsReceiptNote` | `store_goodsreceiptnote` | 38 | 7 | **DELETE** |
| **Purchase** | `purchase.QuotationComparison`| `purchase_quotationcomparison`| 7 | 0 | **DELETE** |
| | `purchase.SupplierQuotation` | `purchase_supplierquotation` | 23 | 0 | **DELETE** |
| | `purchase.RequestForQuotation`| `purchase_requestforquotation`| 6 | 0 | **DELETE** |
| | `purchase.PurchaseReturn` | `purchase_purchasereturn` | 0 | 0 | Clean |
| | `purchase.PurchaseOrder` | `purchase_purchaseorder` | 40 | 7 | **DELETE** |
| | `purchase.PurchaseRequisition`| `purchase_purchaserequisition`| 32 | 6 | **DELETE** |
| | `purchase.MaterialRequirement`| `purchase_materialrequirement`| 76 | 6 | **DELETE** |
| **Design & Eng** | `designer.DesignRevisionLog` | `designer_designrevisionlog` | 0 | 0 | Clean |
| | `designer.TechnicalDocumentItem`| `designer_technicaldocumentitem`| 0 | 0 | Clean |
| | `designer.DesignTask` | `designer_designtask` | 4 | 0 | **DELETE** |
| | `designer.AssemblyDrawing` | `designer_assemblydrawing` | 2 | 0 | **DELETE** |
| | `designer.Drawing2D` | `designer_drawing2d` | 8 | 1 | **DELETE** |
| | `designer.Design3DModel` | `designer_design3dmodel` | 2 | 1 | **DELETE** |
| | `designer.CustomerRequirement`| `designer_customerrequirement`| 7 | 1 | **DELETE** |
| | `designer.BOMHeader` | `designer_bomheader` | 24 | 8 | **DELETE** |
| | `designer.DesignJob` | `designer_designjob` | 34 | 7 | **DELETE** |
| **Project Mgmt** | `projects.CustomerChangeRequest`| `projects_customerchangerequest`| 0 | 0 | Clean |
| | `projects.ProjectIssue` | `projects_projectissue` | 0 | 0 | Clean |
| | `projects.ProjectDelay` | `projects_projectdelay` | 0 | 0 | Clean |
| | `projects.ProjectCost` | `projects_projectcost` | 0 | 0 | Clean |
| | `projects.ProjectDocument` | `projects_projectdocument` | 2 | 0 | **DELETE** |
| | `projects.DepartmentAssignment`| `projects_departmentassignment`| 5 | 0 | **DELETE** |
| | `projects.ProjectTask` | `projects_projecttask` | 140 | 3 | **DELETE** |
| | `projects.ProjectMilestone` | `projects_projectmilestone` | 6 | 5 | **DELETE** |
| | `projects.ProjectPlanningStage`| `projects_projectplanningstage`| 763 | 144 | **DELETE** |
| | `projects.ProjectJobMaster` | `projects_projectjobmaster` | 38 | 8 | **DELETE** |
| **CRM & Sales** | `crm.Activity` | `crm_activity` | 0 | 0 | Clean |
| | `crm.FollowUp` | `crm_followup` | 47 | 2 | **DELETE** |
| | `crm.SiteVisit` | `crm_sitevisit` | 1 | 1 | **DELETE** |
| | `crm.SalesOrder` | `crm_salesorder` | 56 | 8 | **DELETE** |
| | `crm.CustomerPO` | `crm_customerpo` | 60 | 8 | **DELETE** |
| | `crm.Quotation` | `crm_quotation` | 65 | 8 | **DELETE** |
| | `crm.Opportunity` | `crm_opportunity` | 51 | 8 | **DELETE** |
| | `crm.Enquiry` | `crm_enquiry` | 58 | 15 | **DELETE** |
| | `crm.Lead` | `crm_lead` | 64 | 37 | **DELETE** |
| **Category D Total** | | | **2,519** | **434** | **SLATED FOR RESET** |

---

## 5. Ambiguous / Demo Entity Master Records (For Client Review)

The automated scanner detected **18 potential test/mock records** within tables that are traditionally preserved as Masters (`crm.Customer` and `store.ItemMaster`):

```
Model                  | ID / Code            | Name / Description                   | Flag Reason
-------------------------------------------------------------------------------------------------------------------
crm.Customer           | CUST-2026-0005       | Audit Petrochem Ltd                  | Matches test keyword in company name
crm.Customer           | CUST-2026-0006       | Audit Petrochem Ltd                  | Matches test keyword in company name
crm.Customer           | CUST-2026-0007       | Audit Petrochem Ltd                  | Matches test keyword in company name
crm.Customer           | CUST-2026-0008       | Audit Petrochem Ltd                  | Matches test keyword in company name
crm.Customer           | CUST-2026-0009       | Audit Petrochem Ltd                  | Matches test keyword in company name
crm.Customer           | CUST-2026-0028       | Traceability Industries Ltd QA-2498  | Matches test keyword in company name
crm.Customer           | CUST-2026-0029       | Traceability Industries Ltd QA-2098  | Matches test keyword in company name
crm.Customer           | CUST-2026-0030       | Report Audit Client QA-7989          | Matches test keyword in company name
crm.Customer           | CUST-2026-0031       | test 1 Aluminium PVT LTD             | Matches test keyword in company name
crm.Customer           | CUST-2026-0032       | E2E Manufacturing Pvt Ltd            | Matches test keyword in company name
crm.Customer           | CUST-2026-0033       | E2E Manufacturing Pvt Ltd            | Matches test keyword in company name
crm.Customer           | CUST-2026-0036       | test2                                | Matches test keyword in company name
crm.Customer           | CUST-2026-0037       | test2                                | Matches test keyword in company name
crm.Customer           | CUST-2026-0039       | test 3 Aluminium PVT LTD             | Matches test keyword in company name
crm.Customer           | CUST-2026-0040       | Test 4 Aluminium PVT LTD             | Matches test keyword in company name
crm.Customer           | CUST-2026-0041       | test 5 Aluminium PVT LTD             | Matches test keyword in company name
store.ItemMaster       | itm-qa-stock-9234    | QA-STOCK-9234: SS304 Flange 150mm Q  | Matches test keyword in item master
store.ItemMaster       | itm-itm-01           | ITM-01: Test Item                    | Matches test keyword in item master
```

### Recommendation on Masters:
1. **Default Go-Live Scope (Recommended):** Keep genuine suppliers (`Jindal Stainless`, `ABB India`), genuine reference materials (`SS 316L Plates`, etc.), and customer master entities intact while removing all transactions.
2. **Alternative (Full Clean Slate):** If the client wishes to enter all customer and item masters from scratch, specify `--include-demo-masters`.

---

## 6. Implementation of the Management Command

A new production management command has been implemented in:
`apps/core/management/commands/cleanup_testing_data.py`

### Key Safety Characteristics:
1. **Dry-Run by Default:** Running without `--execute` or with `--dry-run` performs a non-destructive read-only simulation.
2. **Atomic Transaction:** Wrapped in `transaction.atomic()` to guarantee all-or-nothing execution.
3. **Dependency Topological Ordering:** Deletes dependent child records (e.g. Sales Invoices, Goods Receipts, Material Issues, Stock Ledgers) before parent records (e.g. Sales Orders, Customer POs, Quotations, Leads).
4. **Mandatory Confirmation Passphrase:** Live execution requires `--confirm-go-live "CONFIRM-CLEANUP-UMAERP-2026"`.
5. **Stock Balance Zeroing:** Synchronously resets `store.StockBalance` so no ghost stock quantities remain after deleting GRNs and stock ledgers.
6. **Post-Cleanup Verification:** Automatically verifies that all 68 transaction models reached 0 rows.

---

## 7. Sandbox Execution Evidence

To verify execution without altering live data, a binary clone of the production backup was executed with `--execute`:

```
[CONFIRMED] Commencing atomic transaction deletion...
Executing transaction deletions in dependency order...
  [OK] Cleaned integration.ApprovalItem: 4 records deleted.
  [OK] Cleaned integration.ERPAlertItem: 4 records deleted.
  [OK] Cleaned core.Notification: 479 records deleted.
  [OK] Cleaned accounting.ContraVoucher: 1 records deleted.
  [OK] Cleaned accounting.JobCostingSummary: 2 records deleted.
  [OK] Cleaned accounting.JournalEntry: 1 records deleted.
  [OK] Cleaned accounting.SupplierPayment: 5 records deleted.
  [OK] Cleaned accounting.CustomerReceipt: 21 records deleted.
  [OK] Cleaned accounting.PurchaseInvoice: 2 records deleted.
  [OK] Cleaned accounting.SalesInvoice: 12 records deleted.
  [OK] Cleaned maintenance.ServiceVisit: 2 records deleted.
  [OK] Cleaned maintenance.BreakdownRecord: 1 records deleted.
  [OK] Cleaned maintenance.ServiceRequest: 1 records deleted.
  [OK] Cleaned maintenance.PreventiveMaintenancePlan: 1 records deleted.
  [OK] Cleaned maintenance.AMCContract: 1 records deleted.
  [OK] Cleaned hr.LeaveRequest: 1 records deleted.
  [OK] Cleaned hr.AttendanceRecord: 3 records deleted.
  [OK] Cleaned hr.PayrollRecord: 3 records deleted.
  [OK] Cleaned hr.EmployeeOnboarding: 1 records deleted.
  [OK] Cleaned hr.SalaryStructure: 2 records deleted.
  [OK] Cleaned production.DispatchOrder: 12 records deleted.
  [OK] Cleaned production.FinishedGoodsItem: 39 records deleted.
  [OK] Cleaned production.ProductionScrap: 2 records deleted.
  [OK] Cleaned production.ReworkOrder: 2 records deleted.
  [OK] Cleaned production.ProductionHold: 2 records deleted.
  [OK] Cleaned production.WIPRecord: 1 records deleted.
  [OK] Cleaned production.ProductionEntry: 5 records deleted.
  [OK] Cleaned production.ProductionScheduleItem: 6 records deleted.
  [OK] Cleaned production.ProductionOrder: 5 records deleted.
  [OK] Cleaned production.WorkOrder: 67 records deleted.
  [OK] Cleaned production.ProductionPlan: 6 records deleted.
  [OK] Cleaned production.ProductionMaterialRequest: 7 records deleted.
  [OK] Cleaned production.ManufacturingJob: 3 records deleted.
  [OK] Cleaned store.MaterialReturn: 1 records deleted.
  [OK] Cleaned store.MaterialIssue: 24 records deleted.
  [OK] Cleaned store.StockLedgerEntry: 80 records deleted.
  [OK] Cleaned store.StockBalance: 17 records deleted.
  [OK] Cleaned store.QCInspection: 34 records deleted.
  [OK] Cleaned store.GoodsReceiptNote: 38 records deleted.
  [OK] Cleaned purchase.QuotationComparison: 7 records deleted.
  [OK] Cleaned purchase.SupplierQuotation: 23 records deleted.
  [OK] Cleaned purchase.RequestForQuotation: 6 records deleted.
  [OK] Cleaned purchase.PurchaseOrder: 40 records deleted.
  [OK] Cleaned purchase.PurchaseRequisition: 32 records deleted.
  [OK] Cleaned purchase.MaterialRequirement: 76 records deleted.
  [OK] Cleaned designer.DesignTask: 4 records deleted.
  [OK] Cleaned designer.AssemblyDrawing: 2 records deleted.
  [OK] Cleaned designer.Drawing2D: 8 records deleted.
  [OK] Cleaned designer.Design3DModel: 2 records deleted.
  [OK] Cleaned designer.CustomerRequirement: 7 records deleted.
  [OK] Cleaned designer.BOMHeader: 24 records deleted.
  [OK] Cleaned designer.DesignJob: 34 records deleted.
  [OK] Cleaned projects.ProjectDocument: 2 records deleted.
  [OK] Cleaned projects.DepartmentAssignment: 5 records deleted.
  [OK] Cleaned projects.ProjectTask: 140 records deleted.
  [OK] Cleaned projects.ProjectMilestone: 6 records deleted.
  [OK] Cleaned projects.ProjectPlanningStage: 763 records deleted.
  [OK] Cleaned projects.ProjectJobMaster: 38 records deleted.
  [OK] Cleaned crm.FollowUp: 47 records deleted.
  [OK] Cleaned crm.SiteVisit: 1 records deleted.
  [OK] Cleaned crm.SalesOrder: 56 records deleted.
  [OK] Cleaned crm.CustomerPO: 60 records deleted.
  [OK] Cleaned crm.Quotation: 65 records deleted.
  [OK] Cleaned crm.Opportunity: 51 records deleted.
  [OK] Cleaned crm.Enquiry: 58 records deleted.
  [OK] Cleaned crm.Lead: 64 records deleted.

[TRANSACTION COMMITTED] All targeted testing transactions removed successfully!

[POST-CLEANUP VERIFICATION] Checking transaction counts:
  [PASS] All transaction models verified at 0 rows.
```

---

## 8. Client Decisions Required Before Live Execution

Before executing the live cleanup on the production database, please provide decisions on the following 3 items:

1. **Target Environment Scope:**
   * Execute cleanup on **Live PythonAnywhere Production Database** (`/home/umaERP/BE-ERP-UMA/db.sqlite3`)?
   * Execute cleanup on **Local Development Database** (`d:\UMA ERP\BE-ERP-UMA\db.sqlite3`)?
   * Or both?

2. **Entity Masters (Customers & Suppliers):**
   * **Option A (Recommended):** Preserve all Customer and Supplier Master entries (only reset transactions: Leads, Quotations, Orders, Invoices).
   * **Option B:** Wipe demo/test customer and supplier entities as well, so the client begins with completely empty master lists.

3. **Document Auto-Numbering Counters:**
   * **Option A (Recommended):** Reset all `core.NumberingSetting` counters back to `0` / starting sequence `0001` for go-live.
   * **Option B:** Keep current numbering sequence offsets.

---

## 9. Next Steps (Upon Approval)

Once you approve the decisions above:
1. Sync `cleanup_testing_data.py` to the deployed server.
2. Execute `python manage.py cleanup_testing_data --execute --confirm-go-live "CONFIRM-CLEANUP-UMAERP-2026"` with your chosen options.
3. Reload web app on PythonAnywhere.
4. Verify Django Admin and UI empty states live.
