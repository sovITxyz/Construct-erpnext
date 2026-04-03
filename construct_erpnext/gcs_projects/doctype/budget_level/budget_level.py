import frappe
from frappe.model.document import Document


class BudgetLevel(Document):
	def before_save(self):
		self.compute_estimated_total()
		self.compute_variance()

	def compute_estimated_total(self):
		self.estimated_total = (self.estimated_qty or 0) * (self.estimated_unit_cost or 0)

	def compute_variance(self):
		self.variance = (self.estimated_total or 0) - (self.real_total or 0)
