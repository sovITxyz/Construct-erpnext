import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ProjectRevenue(Document):
	def validate(self):
		self.compute_remaining()

	def compute_remaining(self):
		self.remaining_amount = flt(self.negotiated_amount) - flt(self.invoiced_amount)
