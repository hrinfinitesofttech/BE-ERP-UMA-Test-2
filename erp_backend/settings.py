"""
Django settings for erp_backend project.
"""

from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-_tw-q!k8uoy6r-pwiw4q$cb0v^#nxk2s!n0w*azzy7jbvlqs6c'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',

    # Local apps
    'apps.core',
    'apps.organization',
    'apps.authentication',
    'apps.crm',
    'apps.projects',
    'apps.designer',
    'apps.purchase',
    'apps.store',
    'apps.production',
    'apps.maintenance',
    'apps.hr',
    'apps.accounting',
    'apps.integration',
]

try:
    import jazzmin
    INSTALLED_APPS.insert(0, 'jazzmin')
except ImportError:
    pass

AUTH_USER_MODEL = 'authentication.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# JAZZMIN MODERN ADMIN THEME SETTINGS
# ==============================================================================
JAZZMIN_SETTINGS = {
    "site_title": "UMA TECHNO FAB | Manufacturing ERP",
    "site_header": "UMA TECHNO FAB",
    "site_brand": "UMA TECHNO FAB",
    "site_logo_classes": "img-circle",
    "welcome_sign": "UMA TECHNO FAB - Manufacturing ERP Admin",
    "copyright": "UMA TECHNO FAB | Quality • Innovation • Partnership",
    "search_model": ["crm.Customer"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Launch Frontend ERP", "url": "http://localhost:3000", "new_window": True},
        {"model": "authentication.User"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "crm",
        "projects",
        "designer",
        "purchase",
        "store",
        "production",
        "accounting",
        "maintenance",
        "hr",
        "integration",
        "authentication",
        "organization",
        "core",
    ],
    "icons": {
        "auth": "fas fa-shield-alt",
        "auth.Group": "fas fa-users-cog",
        "authentication.User": "fas fa-user-shield",
        "authentication.Employee": "fas fa-id-badge",
        "organization.Department": "fas fa-building",
        "organization.Role": "fas fa-user-tag",
        "core.CompanySetting": "fas fa-cogs",
        "core.NumberingSetting": "fas fa-sort-numeric-down",
        "core.AuditLog": "fas fa-history",
        "core.Notification": "fas fa-bell",
        "core.BugTicket": "fas fa-bug",
        "core.BackupRecord": "fas fa-database",
        "core.DataImportLog": "fas fa-file-import",
        "core.SecurityCheckRecord": "fas fa-user-lock",
        "core.GoLiveChecklistItem": "fas fa-tasks",

        # CRM & Sales
        "crm.Lead": "fas fa-funnel-dollar",
        "crm.Customer": "fas fa-users",
        "crm.Contact": "fas fa-address-book",
        "crm.Enquiry": "fas fa-question-circle",
        "crm.Opportunity": "fas fa-handshake",
        "crm.FollowUp": "fas fa-phone-volume",
        "crm.SiteVisit": "fas fa-map-marked-alt",
        "crm.Exhibition": "fas fa-store-alt",
        "crm.Quotation": "fas fa-file-invoice-dollar",
        "crm.CustomerPO": "fas fa-file-contract",
        "crm.SalesOrder": "fas fa-shopping-bag",
        "crm.Activity": "fas fa-tasks",

        # Project & Job Management
        "projects.ProjectJobMaster": "fas fa-briefcase",
        "projects.ProjectPlanningStage": "fas fa-stream",
        "projects.ProjectMilestone": "fas fa-flag-checkered",
        "projects.ProjectTask": "fas fa-check-double",
        "projects.DepartmentAssignment": "fas fa-network-wired",
        "projects.ProjectIssue": "fas fa-exclamation-triangle",
        "projects.ProjectDelay": "fas fa-hourglass-half",
        "projects.CustomerChangeRequest": "fas fa-exchange-alt",
        "projects.ProjectCost": "fas fa-coins",
        "projects.ProjectDocument": "fas fa-folder-open",

        # Designer & Engineering
        "designer.DesignJob": "fas fa-palette",
        "designer.CustomerRequirement": "fas fa-clipboard-list",
        "designer.Drawing2D": "fas fa-draw-polygon",
        "designer.Design3DModel": "fas fa-cube",
        "designer.AssemblyDrawing": "fas fa-layer-group",
        "designer.BOMHeader": "fas fa-sitemap",
        "designer.DesignRevisionLog": "fas fa-code-branch",
        "designer.TechnicalDocumentItem": "fas fa-file-alt",
        "designer.DesignTask": "fas fa-pencil-ruler",

        # Purchase Management
        "purchase.Supplier": "fas fa-truck",
        "purchase.SupplierContact": "fas fa-address-card",
        "purchase.PurchaseRequisition": "fas fa-file-signature",
        "purchase.RequestForQuotation": "fas fa-envelope-open-text",
        "purchase.SupplierQuotation": "fas fa-receipt",
        "purchase.QuotationComparison": "fas fa-balance-scale",
        "purchase.PurchaseOrder": "fas fa-shopping-cart",
        "purchase.PurchaseReturn": "fas fa-undo-alt",
        "purchase.MaterialRequirement": "fas fa-boxes",

        # Store & Warehouse
        "store.ItemCategory": "fas fa-tags",
        "store.UOMMaster": "fas fa-ruler",
        "store.ItemMaster": "fas fa-box-open",
        "store.Warehouse": "fas fa-warehouse",
        "store.WarehouseLocation": "fas fa-map-marker-alt",
        "store.GoodsReceiptNote": "fas fa-dolly-flatbed",
        "store.QCInspection": "fas fa-clipboard-check",
        "store.StockBalance": "fas fa-cubes",
        "store.StockReservation": "fas fa-lock",
        "store.MaterialIssue": "fas fa-arrow-circle-right",
        "store.MaterialReturn": "fas fa-arrow-circle-left",
        "store.StockTransfer": "fas fa-dolly",
        "store.StockAdjustment": "fas fa-sliders-h",
        "store.StockLedgerEntry": "fas fa-book",
        "store.ScrapEntry": "fas fa-trash-alt",

        # Production & Shop Floor
        "production.ManufacturingJob": "fas fa-industry",
        "production.ProductionPlan": "fas fa-calendar-alt",
        "production.WorkCenter": "fas fa-cog",
        "production.RoutingOperation": "fas fa-bezier-curve",
        "production.WorkOrder": "fas fa-clipboard",
        "production.ProductionOrder": "fas fa-cogs",
        "production.ProductionScheduleItem": "fas fa-calendar-check",
        "production.ProductionEntry": "fas fa-hammer",
        "production.WIPRecord": "fas fa-spinner",
        "production.ProductionHold": "fas fa-pause-circle",
        "production.ReworkOrder": "fas fa-wrench",
        "production.ProductionScrap": "fas fa-recycle",
        "production.FinishedGoodsItem": "fas fa-check-circle",
        "production.ProductionMaterialRequest": "fas fa-cart-arrow-down",

        # Accounting & Finance
        "accounting.FinancialYear": "fas fa-calendar",
        "accounting.ChartOfAccount": "fas fa-sitemap",
        "accounting.TaxMaster": "fas fa-percentage",
        "accounting.CostCenter": "fas fa-calculator",
        "accounting.SalesInvoice": "fas fa-file-invoice",
        "accounting.PurchaseInvoice": "fas fa-file-invoice-dollar",
        "accounting.CustomerReceipt": "fas fa-cash-register",
        "accounting.SupplierPayment": "fas fa-money-bill-alt",
        "accounting.JournalEntry": "fas fa-book-open",
        "accounting.JobCostingSummary": "fas fa-chart-line",
        "accounting.CreditNote": "fas fa-sticky-note",
        "accounting.DebitNote": "fas fa-receipt",
        "accounting.BankAccount": "fas fa-university",
        "accounting.ContraVoucher": "fas fa-exchange-alt",
        "accounting.ExpenseEntry": "fas fa-funnel-dollar",
        "accounting.FixedAsset": "fas fa-coins",

        # Maintenance & Services
        "maintenance.InternalAsset": "fas fa-server",
        "maintenance.CustomerMachine": "fas fa-robot",
        "maintenance.ServiceRequest": "fas fa-headset",
        "maintenance.PreventiveMaintenancePlan": "fas fa-shield-virus",
        "maintenance.BreakdownRecord": "fas fa-car-crash",
        "maintenance.ServiceVisit": "fas fa-user-clock",
        "maintenance.AMCContract": "fas fa-file-contract",
        "maintenance.ServiceWorkOrder": "fas fa-tools",
        "maintenance.ServicePartIssue": "fas fa-dolly",
        "maintenance.ServicePartReturn": "fas fa-undo",
        "maintenance.ServiceReport": "fas fa-file-signature",
        "maintenance.WarrantyRecord": "fas fa-award",
        "maintenance.ServiceContract": "fas fa-handshake",
        "maintenance.DowntimeRecord": "fas fa-stopwatch",

        # HR & Payroll
        "hr.Designation": "fas fa-id-card",
        "hr.EmployeeDocument": "fas fa-file-contract",
        "hr.ShiftMaster": "fas fa-business-time",
        "hr.AttendanceRecord": "fas fa-user-clock",
        "hr.LeaveRequest": "fas fa-plane-departure",
        "hr.WFHRequest": "fas fa-laptop-house",
        "hr.MissedPunchRequest": "fas fa-fingerprint",
        "hr.AttendanceRegularization": "fas fa-user-check",
        "hr.OvertimeRecord": "fas fa-clock",
        "hr.EarlyCheckoutRequest": "fas fa-running",
        "hr.SalaryComponent": "fas fa-money-bill-wave",
        "hr.SalaryStructure": "fas fa-wallet",
        "hr.PayrollRecord": "fas fa-money-check-alt",
        "hr.EmployeeAdvanceLoan": "fas fa-hand-holding-usd",
        "hr.ReimbursementExpense": "fas fa-receipt",
        "hr.Holiday": "fas fa-calendar-day",
        "hr.EmployeeOnboarding": "fas fa-user-plus",
        "hr.EmployeeTransfer": "fas fa-people-arrows",
        "hr.EmployeePromotion": "fas fa-level-up-alt",
        "hr.EmployeeExit": "fas fa-user-minus",
        "hr.EmployeeAppraisal": "fas fa-star",

        # Integration & 360°
        "integration.ApprovalItem": "fas fa-stamp",
        "integration.ERPAlertItem": "fas fa-exclamation-circle",
        "integration.Job360Overview": "fas fa-circle-notch",
        "integration.Customer360Summary": "fas fa-id-card-alt",
        "integration.Supplier360Summary": "fas fa-truck-loading",
        "integration.ItemMaterial360Summary": "fas fa-boxes",
        "integration.Employee360Summary": "fas fa-user-astronaut",
        "integration.JobProfitabilityRecord": "fas fa-dollar-sign",
        "integration.GlobalActivityLog": "fas fa-stream",
        "integration.ExecutiveDashboardKPI": "fas fa-tachometer-alt",
        "integration.ERPReportCenterItem": "fas fa-chart-pie",
    },
    "default_icon_parents": "fas fa-chevron-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "css/custom_admin.css",
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "authentication.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-light",
    "accent": "accent-warning",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Trusted Origins (Required for PythonAnywhere and Vercel frontend)
CSRF_TRUSTED_ORIGINS = [
    'https://*.pythonanywhere.com',
    'https://erpuma.pythonanywhere.com',
    'https://*.vercel.app',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Django REST Framework Settings
try:
    import djangorestframework_camel_case  # noqa: F401
    DEFAULT_RENDERER_CLASSES = (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
    )
    DEFAULT_PARSER_CLASSES = (
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'rest_framework.parsers.JSONParser',
    )
except ImportError:
    DEFAULT_RENDERER_CLASSES = (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
    DEFAULT_PARSER_CLASSES = (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    )

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDERER_CLASSES,
    'DEFAULT_PARSER_CLASSES': DEFAULT_PARSER_CLASSES,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
