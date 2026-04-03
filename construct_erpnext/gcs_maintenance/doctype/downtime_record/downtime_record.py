# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class DowntimeRecord(Document):
	def validate(self):
		self.compute_duration_hours()

	def compute_duration_hours(self):
		if self.start_datetime and self.end_datetime:
			self.duration_hours = round(time_diff_in_hours(self.end_datetime, self.start_datetime), 2)
		else:
			self.duration_hours = 0
