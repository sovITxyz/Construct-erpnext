import frappe
from frappe.model.document import Document
from frappe.utils import flt


class MaterialDistribution(Document):
	def validate(self):
		self.compute_totals()

	def compute_totals(self):
		total = 0
		for row in self.items or []:
			row.amount = flt(row.qty) * flt(row.rate)
			total += flt(row.amount)
		self.total_cost = total
