# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def calculate_withholdings(doc, method):
	"""Calculate tax withholdings on a Purchase Invoice during validation.

	Called via doc_events hook on Purchase Invoice validate.
	Applies El Salvador-specific withholding rules:
	  1. ISR 10% on services from personas naturales
	  2. IVA 1% retention when company is Gran Contribuyente
	  3. Generic retention fallback for manually configured suppliers
	"""
	if not doc.supplier:
		return

	# Get supplier info
	supplier = frappe.get_cached_doc("Supplier", doc.supplier)

	grand_total = flt(doc.grand_total) or flt(doc.total)
	if grand_total <= 0:
		return

	# Get company info
	company_doc = frappe.get_cached_doc("Company", doc.company)
	is_gran_contribuyente = getattr(company_doc, "sv_gran_contribuyente", 0)

	# 1. ISR Withholding (10% on services from personas naturales)
	_apply_isr_withholding(doc, supplier, grand_total)

	# 2. IVA 1% Retention (only if company is Gran Contribuyente
	#    and supplier is NOT Gran Contribuyente)
	if is_gran_contribuyente:
		_apply_iva_retention(doc, supplier, grand_total)

	# 3. Generic retention (fallback for manually configured retention_percentage)
	_apply_generic_retention(doc, supplier, grand_total)


def _apply_isr_withholding(doc, supplier, grand_total):
	"""Apply 10% ISR withholding for services from individuals (personas naturales)."""
	supplier_type = getattr(supplier, "sv_taxpayer_type", "")
	retention_pct = flt(getattr(supplier, "retention_percentage", 0))

	# ISR withholding applies when supplier is a persona natural providing services.
	# Check if the supplier has ISR-specific retention configured.
	if supplier_type != "Persona Natural" or retention_pct <= 0:
		# If no explicit retention_percentage, check if 10% ISR should apply.
		# Default: don't auto-apply, let user configure per-supplier.
		return

	isr_amount = flt(grand_total * 0.10, 2)
	if isr_amount <= 0:
		return

	isr_account = _get_isr_account(doc.company)
	if not isr_account:
		return

	_upsert_tax_row(doc, isr_account, isr_amount, _("ISR Withholding 10%"))


def _apply_iva_retention(doc, supplier, grand_total):
	"""Apply 1% IVA advance retention when company is Gran Contribuyente."""
	supplier_type = getattr(supplier, "sv_taxpayer_type", "")

	# Gran Contribuyente retains 1% IVA from non-gran-contribuyente suppliers
	if supplier_type == "Gran Contribuyente":
		return  # No retention between gran contribuyentes

	iva_retention_amount = flt(grand_total * 0.01, 2)
	if iva_retention_amount <= 0:
		return

	iva_ret_account = _get_iva_retention_account(doc.company)
	if not iva_ret_account:
		return

	_upsert_tax_row(doc, iva_ret_account, iva_retention_amount, _("IVA Retention 1%"))


def _apply_generic_retention(doc, supplier, grand_total):
	"""Fallback: apply generic retention_percentage from Supplier."""
	retention_pct = flt(getattr(supplier, "retention_percentage", 0))
	if not retention_pct or retention_pct <= 0:
		return

	# Skip if ISR already applied (to avoid double-deducting)
	isr_account = _get_isr_account(doc.company)
	for tax_row in doc.get("taxes", []):
		if tax_row.account_head == isr_account and tax_row.add_deduct_tax == "Deduct":
			return

	withholding_amount = flt(grand_total * retention_pct / 100, 2)
	if withholding_amount <= 0:
		return

	withholding_account = _get_withholding_account(doc.company)
	_upsert_tax_row(
		doc, withholding_account, withholding_amount,
		_("Tax Withholding ({0}%)").format(retention_pct),
	)


def _upsert_tax_row(doc, account_head, amount, description):
	"""Add or update a deduction tax row."""
	for tax_row in doc.get("taxes", []):
		if tax_row.account_head == account_head and tax_row.add_deduct_tax == "Deduct":
			tax_row.tax_amount = -abs(amount)
			tax_row.description = description
			return

	doc.append("taxes", {
		"category": "Total",
		"add_deduct_tax": "Deduct",
		"charge_type": "Actual",
		"account_head": account_head,
		"tax_amount": -abs(amount),
		"description": description,
	})


def _get_isr_account(company):
	"""Get the ISR withholding account for the given company."""
	account = frappe.db.get_value(
		"Account",
		{"account_name": ["like", "%Retenci\u00f3n ISR%"], "company": company},
		"name",
	)
	if not account:
		account = _get_withholding_account(company)
	return account


def _get_iva_retention_account(company):
	"""Get the IVA 1% retention account for the given company."""
	account = frappe.db.get_value(
		"Account",
		{"account_name": ["like", "%Retenci\u00f3n IVA%"], "company": company},
		"name",
	)
	return account


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
