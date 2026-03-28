import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ProjectInvoice(Document):
	def validate(self):
		self.compute_total()

	def compute_total(self):
		total = 0
		for row in self.revenue_items or []:
			total += flt(row.amount)
		self.total_invoice_amount = total
