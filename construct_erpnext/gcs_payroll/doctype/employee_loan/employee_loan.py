# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class EmployeeLoan(Document):
	def validate(self):
		self._validate_amounts()
		self.compute_balance()
		self._auto_update_status()

	def compute_balance(self):
		self.remaining_balance = flt(self.loan_amount) - flt(self.total_deducted)

		if self.remaining_balance < 0:
			self.remaining_balance = 0

		if flt(self.installment_amount):
			self.installments_remaining = max(
				0,
				math.ceil(flt(self.remaining_balance) / flt(self.installment_amount)),
			)
		else:
			self.installments_remaining = 0

	def _validate_amounts(self):
		if flt(self.loan_amount) <= 0:
			frappe.throw(_("Loan Amount must be greater than zero."))

		if flt(self.installment_amount) <= 0:
			frappe.throw(_("Installment Amount must be greater than zero."))

		if flt(self.total_deducted) < 0:
			frappe.throw(_("Total Deducted cannot be negative."))

		if flt(self.total_deducted) > flt(self.loan_amount):
			frappe.throw(
				_("Total Deducted ({0}) cannot exceed Loan Amount ({1}).").format(
					flt(self.total_deducted), flt(self.loan_amount)
				)
			)

	def _auto_update_status(self):
		"""Automatically mark as Fully Paid when the remaining balance is zero."""
		if self.status == "Cancelled":
			return

		if flt(self.remaining_balance) <= 0:
			self.status = "Fully Paid"
		elif self.status == "Fully Paid" and flt(self.remaining_balance) > 0:
			# Revert if balance was restored (e.g. cancellation of a deduction)
			self.status = "Active"
