import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate


class ActivitySchedule(Document):
	def validate(self):
		self.validate_dates()
		self.compute_duration()

	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(_("End Date cannot be before Start Date."))

	def compute_duration(self):
		if self.start_date and self.end_date:
			self.duration_days = date_diff(self.end_date, self.start_date) + 1
