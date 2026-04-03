# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from frappe.model.document import Document


class AlternativePaymentDocument(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))

		if not self.beneficiary:
			frappe.throw(_("Beneficiary is required"))

	def on_submit(self):
		"""Create a Payment Entry for this alternative payment."""
		if not self.bank_account:
			frappe.throw(_("Bank Account is required to submit"))

		bank_account_doc = frappe.get_doc("Bank Account", self.bank_account)
		if not bank_account_doc.account:
			frappe.throw(
				_("Bank Account {0} does not have a linked GL account").format(
					self.bank_account
				)
			)

		paid_from_account = bank_account_doc.account

		# Determine paid_to account (default payable)
		default_payable = frappe.get_cached_value(
			"Company", self.company, "default_payable_account"
		)
		if not default_payable:
			frappe.throw(
				_("Default Payable Account not configured for company {0}").format(
					self.company
				)
			)

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Pay"
		pe.company = self.company
		pe.paid_amount = flt(self.amount)
		pe.received_amount = flt(self.amount)
		pe.paid_from = paid_from_account
		pe.paid_to = default_payable
		pe.reference_no = self.reference_number or self.name
		pe.reference_date = self.posting_date or nowdate()

		# Map payment_type to mode_of_payment
		mode_map = {
			"Transfer": "Wire Transfer",
			"Card": "Credit Card",
			"Note": "Cash",
			"Other": "Cash",
		}
		pe.mode_of_payment = mode_map.get(self.payment_type, "Cash")

		pe.insert(ignore_permissions=True)
		pe.submit()

		self.db_set("payment_entry", pe.name)
