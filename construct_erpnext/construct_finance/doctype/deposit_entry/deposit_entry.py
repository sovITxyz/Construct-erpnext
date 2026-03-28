# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate
from frappe.model.document import Document


class DepositEntry(Document):
	def validate(self):
		self._compute_total()
		self._validate_deposit_date()

	def _compute_total(self):
		"""Sum up deposit_items amounts and set total_amount."""
		total = 0
		for item in self.get("deposit_items", []):
			total += flt(item.amount)

		if total <= 0:
			frappe.throw(_("Total deposit amount must be greater than zero"))

		self.total_amount = total

	def _validate_deposit_date(self):
		"""Ensure deposit_date is set and not in the future."""
		if not self.deposit_date:
			frappe.throw(_("Deposit Date is required"))

	def on_submit(self):
		"""Create a Journal Entry: debit bank account, credit per deposit item."""
		if not self.bank_account:
			frappe.throw(_("Bank Account is required to submit a Deposit Entry"))

		bank_account_doc = frappe.get_doc("Bank Account", self.bank_account)
		if not bank_account_doc.account:
			frappe.throw(
				_("Bank Account {0} does not have a linked GL account").format(
					self.bank_account
				)
			)

		bank_gl_account = bank_account_doc.account

		# Determine default receivable account
		default_receivable = frappe.get_cached_value(
			"Company", self.company, "default_receivable_account"
		)

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.deposit_date or nowdate()
		je.company = self.company
		je.user_remark = _("Deposit Entry {0}").format(self.name)

		if self.bank_reference:
			je.cheque_no = self.bank_reference
			je.cheque_date = self.deposit_date

		# Debit the bank account for the full amount
		je.append("accounts", {
			"account": bank_gl_account,
			"debit_in_account_currency": flt(self.total_amount),
			"credit_in_account_currency": 0,
		})

		# Credit per deposit item
		for item in self.get("deposit_items", []):
			if flt(item.amount) <= 0:
				continue

			credit_account = default_receivable
			party_type = None
			party = None

			if item.source_type == "Receivable" and item.customer:
				party_type = "Customer"
				party = item.customer

			row = {
				"account": credit_account,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": flt(item.amount),
			}
			if party_type:
				row["party_type"] = party_type
				row["party"] = party

			je.append("accounts", row)

		je.insert(ignore_permissions=True)
		je.submit()
