# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SPCControlChart(Document):
	def validate(self):
		self.validate_control_limits()
		self.evaluate_data_points()

	def validate_control_limits(self):
		if self.lower_control_limit >= self.upper_control_limit:
			frappe.throw("Lower Control Limit must be less than Upper Control Limit.")
		if not (self.lower_control_limit <= self.center_line <= self.upper_control_limit):
			frappe.throw("Center Line must be between Lower and Upper Control Limits.")

	def evaluate_data_points(self):
		"""Mark each data point as in-control or out-of-control."""
		all_in_control = True
		for row in self.data_points:
			row.in_control = int(
				self.lower_control_limit <= row.measured_value <= self.upper_control_limit
			)
			if not row.in_control:
				all_in_control = False

		if self.data_points:
			if all_in_control:
				self.status = "In Control"
			else:
				self.status = "Out of Control"
