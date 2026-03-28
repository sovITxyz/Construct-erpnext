# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import math

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class EmployeeLoan(Document):
	def validate(self):
		self.compute_balance()

	def compute_balance(self):
		self.remaining_balance = flt(self.loan_amount) - flt(self.total_deducted)
		if flt(self.installment_amount):
			self.installments_remaining = math.ceil(
				flt(self.remaining_balance) / flt(self.installment_amount)
			)
		else:
			self.installments_remaining = 0
