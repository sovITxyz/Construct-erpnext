from frappe import _

app_name = "construct_erpnext"
app_title = "Construct ERPNext"
app_publisher = "Sovereign IT Services"
app_description = "Construction ERP portal for ERPNext v16 - replicating o4bi.com features"
app_email = "git@sovit.xyz"
app_license = "AGPL-3.0"
required_apps = ["frappe", "erpnext", "hrms"]

# --- After Install ---
after_install = "construct_erpnext.setup.install.after_install"

# --- Asset Bundles ---
app_include_js = "/assets/construct_erpnext/js/construct_erpnext.bundle.js"
app_include_css = "/assets/construct_erpnext/css/construct_erpnext.bundle.css"

# --- Client Scripts for Stock DocTypes ---
doctype_js = {
    "Project": "public/js/project.js",
    "Task": "public/js/task.js",
    "Asset": "public/js/asset.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Salary Slip": "public/js/salary_slip.js",
}

# --- Override Stock Controllers ---
override_doctype_class = {
    "Project": "construct_erpnext.overrides.project.ConstructProject",
    "Task": "construct_erpnext.overrides.task.ConstructTask",
    "Journal Entry": "construct_erpnext.overrides.journal_entry.ConstructJournalEntry",
    "Salary Slip": "construct_erpnext.overrides.salary_slip.ConstructSalarySlip",
}

# --- Document Events ---
doc_events = {
    "*": {
        "after_insert": "construct_erpnext.construct_security.audit.log_insert",
        "on_update": "construct_erpnext.construct_security.audit.log_update",
        "on_trash": "construct_erpnext.construct_security.audit.log_delete",
    },
    "Purchase Invoice": {
        "on_submit": "construct_erpnext.construct_admin.invoice_auth.check_authorization",
        "validate": "construct_erpnext.construct_admin.tax_withholding.calculate_withholdings",
    },
    "Sales Invoice": {
        "on_submit": "construct_erpnext.construct_admin.reminders.schedule_payment_reminders",
    },
    "Stock Entry": {
        "on_submit": "construct_erpnext.construct_projects.material.assign_cost_to_activity",
    },
    "Salary Slip": {
        "on_submit": "construct_erpnext.construct_payroll.distribution.distribute_costs",
    },
    "Physical Advancement": {
        "on_submit": "construct_erpnext.construct_projects.advancement.update_project_progress",
    },
    "Check Request": {
        "on_update_after_submit": "construct_erpnext.construct_finance.treasury.handle_check_status_change",
    },
}

# --- Scheduler Events ---
scheduler_events = {
    "daily": [
        "construct_erpnext.construct_admin.reminders.send_payment_reminders",
        "construct_erpnext.construct_maintenance.routines.check_preventive_schedules",
    ],
    "hourly": [
        "construct_erpnext.construct_security.audit.process_audit_queue",
    ],
}

# --- Portal ---
portal_menu_items = [
    {"title": _("My Projects"), "route": "/project-portal", "role": "Customer"},
    {"title": _("Invoices"), "route": "/client-invoices", "role": "Customer"},
    {"title": _("Documents"), "route": "/client-documents", "role": "Customer"},
    {"title": _("Authorize Advancement"), "route": "/advancement-auth", "role": "Customer"},
    {"title": _("Payment History"), "route": "/payment-history", "role": "Customer"},
]

website_route_rules = [
    {"from_route": "/project-portal/<project>", "to_route": "project-portal/project"},
    {"from_route": "/advancement-auth/<advancement>", "to_route": "advancement-auth/advancement"},
]

# --- Permissions ---
permission_query_conditions = {
    "Project": "construct_erpnext.construct_security.permissions.project_query_conditions",
    "Task": "construct_erpnext.construct_security.permissions.task_query_conditions",
    "Construction Budget": "construct_erpnext.construct_security.permissions.budget_query_conditions",
}

has_permission = {
    "Project": "construct_erpnext.construct_security.permissions.has_project_permission",
    "Construction Budget": "construct_erpnext.construct_security.permissions.has_budget_permission",
}

# --- Fixtures (Custom Fields on stock doctypes) ---
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "in", [
            "GCS Projects",
            "GCS Production",
            "GCS Maintenance",
            "GCS Admin",
            "GCS Finance",
            "GCS Payroll",
            "GCS Security",
        ]]],
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "in", [
            "GCS Projects",
            "GCS Production",
            "GCS Maintenance",
            "GCS Admin",
            "GCS Finance",
            "GCS Payroll",
            "GCS Security",
        ]]],
    },
    {
        "dt": "Role",
        "filters": [["name", "in", [
            "Construction Manager",
            "Budget Controller",
            "Site Inspector",
            "Construction Client",
            "Subcontractor Portal",
            "Maintenance Engineer",
            "Treasury Manager",
            "Audit Administrator",
            "Payroll Cost Allocator",
        ]]],
    },
]

# --- Jinja Extensions ---
jinja = {
    "methods": [
        "construct_erpnext.construct_projects.utils.get_budget_summary",
        "construct_erpnext.construct_projects.utils.get_advancement_pct",
        "construct_erpnext.construct_portal.utils.get_client_projects",
    ],
}
