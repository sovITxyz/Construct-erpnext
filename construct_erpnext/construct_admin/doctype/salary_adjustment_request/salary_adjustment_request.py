# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SalaryAdjustmentRequest(Document):
	def validate(self):
		self.compute_adjustment()

	def compute_adjustment(self):
		self.adjustment_amount = flt(self.proposed_salary) - flt(self.current_salary)
		if flt(self.current_salary):
			self.adjustment_pct = (flt(self.adjustment_amount) / flt(self.current_salary)) * 100
		else:
			self.adjustment_pct = 0
