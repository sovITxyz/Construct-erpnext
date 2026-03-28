# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, getdate

# Valid status transitions: (from_status, to_status)
_VALID_TRANSITIONS = {
	("Requested", "Approved"),
	("Approved", "Printed"),
	("Printed", "Delivered"),
	# Any status can transition to Cancelled
	("Requested", "Cancelled"),
	("Approved", "Cancelled"),
	("Printed", "Cancelled"),
	("Delivered", "Cancelled"),
}


def handle_check_status_change(doc, method):
	"""Handle status transitions for Check Request documents.

	Called via doc_events hook on Check Request on_update_after_submit.
	"""
	previous = doc.get_doc_before_save()
	if not previous:
		return

	old_status = previous.status
	new_status = doc.status

	if old_status == new_status:
		return

	# Validate transition
	if (old_status, new_status) not in _VALID_TRANSITIONS:
		frappe.throw(
			_("Invalid status transition from {0} to {1}").format(old_status, new_status)
		)

	if new_status == "Approved":
		doc.db_set("approved_by", frappe.session.user)
		doc.db_set("approval_date", nowdate())

	elif new_status == "Printed":
		doc.db_set("print_date", nowdate())

	elif new_status == "Delivered":
		doc.db_set("delivery_date", nowdate())
		if not doc.payment_entry:
			_create_payment_from_check(doc)

	elif new_status == "Cancelled":
		if not doc.cancel_reason:
			frappe.throw(_("Cancel reason is required to cancel a Check Request"))


def _create_payment_from_check(doc):
	"""Create a Payment Entry from a delivered Check Request."""
	if not doc.bank_account:
		frappe.throw(_("Bank Account is required to create a payment"))

	bank_account_doc = frappe.get_doc("Bank Account", doc.bank_account)
	if not bank_account_doc.account:
		frappe.throw(
			_("Bank Account {0} does not have a linked GL account").format(doc.bank_account)
		)
	paid_from_account = bank_account_doc.account

	# Determine the default payable account for the company
	default_payable = frappe.get_cached_value(
		"Company", doc.company, "default_payable_account"
	)
	if not default_payable:
		frappe.throw(
			_("Default Payable Account is not configured for company {0}").format(doc.company)
		)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.party_type = "Supplier"
	pe.party = doc.supplier
	pe.company = doc.company
	pe.paid_amount = doc.amount
	pe.received_amount = doc.amount
	pe.paid_from = paid_from_account
	pe.paid_to = default_payable
	pe.reference_no = doc.check_number or doc.name
	pe.reference_date = doc.delivery_date or nowdate()
	pe.mode_of_payment = "Check"

	# Link back to the purchase invoice if present
	if doc.purchase_invoice:
		outstanding = frappe.db.get_value(
			"Purchase Invoice", doc.purchase_invoice, "outstanding_amount"
		)
		pe.append("references", {
			"reference_doctype": "Purchase Invoice",
			"reference_name": doc.purchase_invoice,
			"allocated_amount": min(doc.amount, outstanding or doc.amount),
		})

	pe.insert(ignore_permissions=True)
	pe.submit()
	doc.db_set("payment_entry", pe.name)
