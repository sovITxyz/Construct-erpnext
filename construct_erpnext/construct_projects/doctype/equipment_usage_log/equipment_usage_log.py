import frappe
from frappe.model.document import Document
from frappe.utils import flt


class EquipmentUsageLog(Document):
	def validate(self):
		self.compute_total_cost()

	def compute_total_cost(self):
		self.total_cost = flt(self.hours_used) * flt(self.cost_rate)
