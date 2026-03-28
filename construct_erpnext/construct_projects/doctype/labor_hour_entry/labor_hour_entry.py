import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class LaborHourEntry(Document):
	def validate(self):
		self.compute_total_cost()
		self.validate_period()

	def compute_total_cost(self):
		self.total_cost = flt(self.hours) * flt(self.rate)

	def validate_period(self):
		if self.period_start and self.period_end:
			if getdate(self.period_end) < getdate(self.period_start):
				frappe.throw(_("Period End cannot be before Period Start."))
