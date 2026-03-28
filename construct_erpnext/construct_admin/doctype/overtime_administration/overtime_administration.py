# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class OvertimeAdministration(Document):
	def validate(self):
		self.compute_total()

	def compute_total(self):
		self.total_amount = flt(self.hours) * flt(self.base_rate) * flt(self.rate_multiplier)
