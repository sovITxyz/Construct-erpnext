# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from frappe.model.document import Document


class CollectionDocument(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))

		if not self.customer:
			frappe.throw(_("Customer is required"))

	def apply_to_invoice(self):
		"""Create a Payment Entry to apply this collection against the linked Sales Invoice."""
		if not self.customer:
			frappe.throw(_("Customer is required to apply collection"))

		if not self.sales_invoice:
			frappe.throw(_("Sales Invoice is required to apply collection"))

		outstanding = flt(
			frappe.db.get_value("Sales Invoice", self.sales_invoice, "outstanding_amount")
		)
		if outstanding <= 0:
			frappe.throw(
				_("Sales Invoice {0} has no outstanding amount").format(self.sales_invoice)
			)

		apply_amount = min(flt(self.amount) - flt(self.applied_amount), outstanding)
		if apply_amount <= 0:
			frappe.throw(_("No remaining amount to apply"))

		default_receivable = frappe.get_cached_value(
			"Company", self.company, "default_receivable_account"
		)
		if not default_receivable:
			frappe.throw(
				_("Default Receivable Account not configured for company {0}").format(
					self.company
				)
			)

		# Determine paid_to account (bank or cash)
		paid_to = None
		if self.bank_reference:
			# Try to find a bank account
			bank_account = frappe.db.get_value(
				"Bank Account",
				{"company": self.company, "is_default": 1},
				"account",
			)
			if bank_account:
				paid_to = bank_account

		if not paid_to:
			paid_to = frappe.get_cached_value(
				"Company", self.company, "default_bank_account"
			) or frappe.get_cached_value(
				"Company", self.company, "default_cash_account"
			)

		if not paid_to:
			frappe.throw(
				_("No default bank or cash account configured for company {0}").format(
					self.company
				)
			)

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.party_type = "Customer"
		pe.party = self.customer
		pe.company = self.company
		pe.paid_amount = apply_amount
		pe.received_amount = apply_amount
		pe.paid_from = default_receivable
		pe.paid_to = paid_to
		pe.reference_no = self.bank_reference or self.name
		pe.reference_date = self.received_date or nowdate()

		pe.append("references", {
			"reference_doctype": "Sales Invoice",
			"reference_name": self.sales_invoice,
			"allocated_amount": apply_amount,
		})

		pe.insert(ignore_permissions=True)
		pe.submit()

		# Update collection document fields
		new_applied = flt(self.applied_amount) + apply_amount
		self.db_set("applied_amount", new_applied)

		if new_applied >= flt(self.amount):
			self.db_set("status", "Applied")
		else:
			self.db_set("status", "Partial")

		return pe.name


@frappe.whitelist()
def apply_collection(collection_name):
	"""Whitelist wrapper to apply a Collection Document to its linked invoice."""
	if not collection_name:
		frappe.throw(_("Collection Document name is required"))

	doc = frappe.get_doc("Collection Document", collection_name)
	pe_name = doc.apply_to_invoice()
	return pe_name
