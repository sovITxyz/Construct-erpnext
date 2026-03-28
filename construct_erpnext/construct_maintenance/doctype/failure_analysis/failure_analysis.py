# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class FailureAnalysis(Document):
	def validate(self):
		self.compute_downtime_hours()

	def compute_downtime_hours(self):
		if self.downtime_start and self.downtime_end:
			self.downtime_hours = round(time_diff_in_hours(self.downtime_end, self.downtime_start), 2)
		else:
			self.downtime_hours = 0
