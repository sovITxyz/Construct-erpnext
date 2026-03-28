# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class AdvancePaymentTracker(Document):
	def validate(self):
		self.compute_remaining()

	def compute_remaining(self):
		self.remaining_amount = flt(self.advance_amount) - flt(self.applied_amount)
