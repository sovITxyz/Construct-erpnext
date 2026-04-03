# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def setup_el_salvador_taxes(company):
    """Set up El Salvador tax accounts and templates for a company."""
    abbr = frappe.get_cached_value("Company", company, "abbr")

    # Find parent accounts
    current_assets = frappe.db.get_value(
        "Account",
        {"company": company, "root_type": "Asset", "is_group": 1, "account_name": "Current Assets"},
        "name",
    )
    current_liabilities = frappe.db.get_value(
        "Account",
        {
            "company": company,
            "root_type": "Liability",
            "is_group": 1,
            "account_name": ["like", "%Current Liabilities%"],
        },
        "name",
    )

    # Create tax accounts
    iva_credit_account = _create_account(
        _("IVA Cr\u00e9dito Fiscal"), company, abbr, current_assets, "Tax", "Asset"
    )
    iva_debit_account = _create_account(
        _("IVA D\u00e9bito Fiscal"), company, abbr, current_liabilities, "Tax", "Liability"
    )
    isr_account = _create_account(
        _("Retenci\u00f3n ISR"), company, abbr, current_liabilities, "Tax", "Liability"
    )
    iva_retention_account = _create_account(
        _("Retenci\u00f3n IVA 1%"), company, abbr, current_liabilities, "Tax", "Liability"
    )

    # Create Tax Category
    if not frappe.db.exists("Tax Category", _("IVA 13%")):
        frappe.get_doc({
            "doctype": "Tax Category",
            "name": _("IVA 13%"),
        }).insert(ignore_permissions=True, ignore_if_duplicate=True)

    # Create Purchase Tax Template - IVA Compras 13%
    purchase_template_name = _("IVA Compras 13% - {0}").format(abbr)
    if not frappe.db.exists("Purchase Taxes and Charges Template", purchase_template_name):
        frappe.get_doc({
            "doctype": "Purchase Taxes and Charges Template",
            "title": _("IVA Compras 13%"),
            "company": company,
            "tax_category": _("IVA 13%"),
            "taxes": [
                {
                    "category": "Total",
                    "add_deduct_tax": "Add",
                    "charge_type": "On Net Total",
                    "account_head": iva_credit_account,
                    "rate": 13,
                    "description": _("IVA 13%"),
                },
            ],
        }).insert(ignore_permissions=True, ignore_if_duplicate=True)

    # Create Sales Tax Template - IVA Ventas 13%
    sales_template_name = _("IVA Ventas 13% - {0}").format(abbr)
    if not frappe.db.exists("Sales Taxes and Charges Template", sales_template_name):
        frappe.get_doc({
            "doctype": "Sales Taxes and Charges Template",
            "title": _("IVA Ventas 13%"),
            "company": company,
            "tax_category": _("IVA 13%"),
            "taxes": [
                {
                    "category": "Total",
                    "add_deduct_tax": "Add",
                    "charge_type": "On Net Total",
                    "account_head": iva_debit_account,
                    "rate": 13,
                    "description": _("IVA 13%"),
                },
            ],
        }).insert(ignore_permissions=True, ignore_if_duplicate=True)

    # Update Company custom fields with the created accounts
    frappe.db.set_value("Company", company, {
        "sv_iva_credit_account": iva_credit_account,
        "sv_iva_debit_account": iva_debit_account,
        "withholding_tax_account": isr_account,
    })

    frappe.msgprint(
        _("El Salvador tax accounts and templates have been created for {0}.").format(company),
        alert=True,
    )


def _create_account(account_name, company, abbr, parent_account, account_type, root_type):
    """Create a ledger account under the given parent, or return it if it already exists."""
    full_name = f"{account_name} - {abbr}"
    if frappe.db.exists("Account", full_name):
        return full_name

    account = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "parent_account": parent_account,
        "company": company,
        "account_type": account_type,
        "root_type": root_type,
        "is_group": 0,
    })
    account.insert(ignore_permissions=True, ignore_if_duplicate=True)
    return account.name
