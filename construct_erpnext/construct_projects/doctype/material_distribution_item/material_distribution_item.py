import frappe
from frappe.model.document import Document


class MaterialDistributionItem(Document):
	def before_save(self):
		self.amount = (self.qty or 0) * (self.rate or 0)
