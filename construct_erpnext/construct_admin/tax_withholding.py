# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def calculate_withholdings(doc, method):
	"""Calculate tax withholdings on a Purchase Invoice during validation.

	Called via doc_events hook on Purchase Invoice validate.
	Checks if the supplier has a retention_percentage custom field, calculates
	the withholding amount, and adds it as a deduction row in the taxes table.
	"""
	if not doc.supplier:
		return

	# Check for pending Withholding Liquidation records to confirm supplier
	# is subject to withholding
	pending_liquidations = frappe.get_all(
		"Withholding Liquidation",
		filters={
			"supplier": doc.supplier,
			"status": "Pending",
		},
		fields=["name"],
		limit=1,
	)

	# Get retention percentage from supplier custom field
	retention_pct = flt(
		frappe.db.get_value("Supplier", doc.supplier, "retention_percentage")
	)

	if not retention_pct or retention_pct <= 0:
		return

	grand_total = flt(doc.grand_total) or flt(doc.total)
	if grand_total <= 0:
		return

	withholding_amount = flt(grand_total * retention_pct / 100, 2)
	if withholding_amount <= 0:
		return

	# Determine withholding account
	withholding_account = _get_withholding_account(doc.company)

	# Check if a withholding deduction row already exists (avoid duplicates)
	for tax_row in doc.get("taxes", []):
		if (
			tax_row.account_head == withholding_account
			and tax_row.add_deduct_tax == "Deduct"
		):
			# Update existing row
			tax_row.tax_amount = -abs(withholding_amount)
			tax_row.description = _("Tax Withholding ({0}%)").format(retention_pct)
			return

	# Add new deduction row
	doc.append("taxes", {
		"category": "Total",
		"add_deduct_tax": "Deduct",
		"charge_type": "Actual",
		"account_head": withholding_account,
		"tax_amount": -abs(withholding_amount),
		"description": _("Tax Withholding ({0}%)").format(retention_pct),
	})


def _get_withholding_account(company):
	"""Get the withholding tax payable account for the given company."""
	# Try to get from company settings (custom field)
	account = frappe.db.get_value("Company", company, "withholding_tax_account")
	if account:
		return account

	# Fallback: look for an account named 'Withholding Tax Payable' in the company
	account = frappe.db.get_value(
		"Account",
		{"account_name": "Withholding Tax Payable", "company": company},
		"name",
	)
	if account:
		return account

	# Last resort: try the default round-off account or throw
	frappe.throw(
		_(
			"Withholding Tax Payable account not found for company {0}. "
			"Please create an account named 'Withholding Tax Payable' or set "
			"the withholding_tax_account field on the Company record."
		).format(company)
	)
