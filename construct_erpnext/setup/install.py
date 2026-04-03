# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def after_install():
    """Run after Construct ERPNext is installed.

    Sets up El Salvador tax and payroll components for companies
    with country = 'El Salvador'.
    """
    sv_companies = frappe.get_all(
        "Company",
        filters={"country": "El Salvador"},
        pluck="name",
    )

    if not sv_companies:
        frappe.logger().info("No El Salvador companies found. Skipping SV setup.")
        return

    for company in sv_companies:
        _setup_company(company)


def _setup_company(company):
    """Run full El Salvador setup for a single company."""
    from construct_erpnext.setup.tax_setup import setup_el_salvador_taxes
    from construct_erpnext.setup.payroll_setup import setup_el_salvador_payroll

    frappe.logger().info(f"Setting up El Salvador localization for {company}")

    try:
        setup_el_salvador_taxes(company)
    except Exception:
        frappe.log_error(
            title=_("El Salvador Tax Setup Error"),
            message=frappe.get_traceback(),
        )

    try:
        setup_el_salvador_payroll(company)
    except Exception:
        frappe.log_error(
            title=_("El Salvador Payroll Setup Error"),
            message=frappe.get_traceback(),
        )

    _create_custom_fields()

    frappe.db.commit()


def _create_custom_fields():
    """Create custom fields on stock DocTypes for El Salvador."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    custom_fields = {
        "Supplier": [
            {
                "fieldname": "sv_taxpayer_type",
                "label": "Taxpayer Type",
                "fieldtype": "Select",
                "options": "\nGran Contribuyente\nMediano Contribuyente\nPeque\u00f1o Contribuyente\nPersona Natural\nOtro",
                "insert_after": "supplier_group",
                "module": "GCS Admin",
                "translatable": 0,
            },
            {
                "fieldname": "retention_percentage",
                "label": "Retention Percentage",
                "fieldtype": "Percent",
                "insert_after": "sv_taxpayer_type",
                "module": "GCS Admin",
                "description": "Tax withholding percentage for this supplier",
            },
            {
                "fieldname": "sv_nit",
                "label": "NIT",
                "fieldtype": "Data",
                "insert_after": "retention_percentage",
                "module": "GCS Admin",
                "description": "N\u00famero de Identificaci\u00f3n Tributaria (0000-000000-000-0)",
            },
            {
                "fieldname": "sv_nrc",
                "label": "NRC",
                "fieldtype": "Data",
                "insert_after": "sv_nit",
                "module": "GCS Admin",
                "description": "N\u00famero de Registro de Contribuyente",
            },
        ],
        "Customer": [
            {
                "fieldname": "sv_taxpayer_type",
                "label": "Taxpayer Type",
                "fieldtype": "Select",
                "options": "\nGran Contribuyente\nMediano Contribuyente\nPeque\u00f1o Contribuyente\nOtro",
                "insert_after": "customer_group",
                "module": "GCS Admin",
            },
            {
                "fieldname": "sv_nit",
                "label": "NIT",
                "fieldtype": "Data",
                "insert_after": "sv_taxpayer_type",
                "module": "GCS Admin",
                "description": "N\u00famero de Identificaci\u00f3n Tributaria (0000-000000-000-0)",
            },
            {
                "fieldname": "sv_nrc",
                "label": "NRC",
                "fieldtype": "Data",
                "insert_after": "sv_nit",
                "module": "GCS Admin",
                "description": "N\u00famero de Registro de Contribuyente",
            },
            {
                "fieldname": "sv_invoice_type",
                "label": "Invoice Type",
                "fieldtype": "Select",
                "options": "\nCCF\nConsumidor Final",
                "insert_after": "sv_nrc",
                "module": "GCS Admin",
                "description": "Default fiscal document type for this customer",
            },
        ],
        "Company": [
            {
                "fieldname": "sv_section_break",
                "label": "El Salvador Settings",
                "fieldtype": "Section Break",
                "insert_after": "default_currency",
                "module": "GCS Admin",
                "collapsible": 1,
            },
            {
                "fieldname": "sv_gran_contribuyente",
                "label": "Large Taxpayer",
                "fieldtype": "Check",
                "insert_after": "sv_section_break",
                "module": "GCS Admin",
                "description": "Check if this company is a Gran Contribuyente",
            },
            {
                "fieldname": "withholding_tax_account",
                "label": "Withholding Tax Account",
                "fieldtype": "Link",
                "options": "Account",
                "insert_after": "sv_gran_contribuyente",
                "module": "GCS Admin",
            },
            {
                "fieldname": "sv_col_break",
                "fieldtype": "Column Break",
                "insert_after": "withholding_tax_account",
                "module": "GCS Admin",
            },
            {
                "fieldname": "sv_iva_credit_account",
                "label": "IVA Credit Account",
                "fieldtype": "Link",
                "options": "Account",
                "insert_after": "sv_col_break",
                "module": "GCS Admin",
            },
            {
                "fieldname": "sv_iva_debit_account",
                "label": "IVA Debit Account",
                "fieldtype": "Link",
                "options": "Account",
                "insert_after": "sv_iva_credit_account",
                "module": "GCS Admin",
            },
        ],
        "Sales Invoice": [
            {
                "fieldname": "sv_document_type",
                "label": "Document Type",
                "fieldtype": "Select",
                "options": "\nCCF\nConsumidor Final\nNota de Cr\u00e9dito\nNota de D\u00e9bito\nExportaci\u00f3n",
                "insert_after": "naming_series",
                "module": "GCS Admin",
            },
            {
                "fieldname": "sv_authorization_number",
                "label": "Authorization Number",
                "fieldtype": "Data",
                "insert_after": "sv_document_type",
                "module": "GCS Admin",
                "description": "DTE authorization number",
            },
        ],
        "Employee": [
            {
                "fieldname": "sv_section_break",
                "label": "El Salvador Information",
                "fieldtype": "Section Break",
                "insert_after": "passport_number",
                "module": "GCS Admin",
                "collapsible": 1,
            },
            {
                "fieldname": "sv_dui",
                "label": "DUI",
                "fieldtype": "Data",
                "insert_after": "sv_section_break",
                "module": "GCS Admin",
                "description": "Documento \u00danico de Identidad (00000000-0)",
            },
            {
                "fieldname": "sv_nit",
                "label": "NIT",
                "fieldtype": "Data",
                "insert_after": "sv_dui",
                "module": "GCS Admin",
                "description": "N\u00famero de Identificaci\u00f3n Tributaria",
            },
            {
                "fieldname": "sv_col_break",
                "fieldtype": "Column Break",
                "insert_after": "sv_nit",
                "module": "GCS Admin",
            },
            {
                "fieldname": "sv_isss_number",
                "label": "ISSS Number",
                "fieldtype": "Data",
                "insert_after": "sv_col_break",
                "module": "GCS Admin",
                "description": "ISSS affiliation number",
            },
            {
                "fieldname": "sv_afp_number",
                "label": "AFP Number",
                "fieldtype": "Data",
                "insert_after": "sv_isss_number",
                "module": "GCS Admin",
                "description": "AFP account number",
            },
            {
                "fieldname": "sv_afp_provider",
                "label": "AFP Provider",
                "fieldtype": "Select",
                "options": "\nAFP Conf\u00eda\nAFP Crecer",
                "insert_after": "sv_afp_number",
                "module": "GCS Admin",
            },
        ],
    }

    create_custom_fields(custom_fields, update=True)
