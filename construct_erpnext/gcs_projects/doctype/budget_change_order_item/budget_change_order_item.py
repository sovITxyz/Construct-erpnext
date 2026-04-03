import frappe
from frappe.model.document import Document


class BudgetChangeOrderItem(Document):
	def before_save(self):
		self.change_amount = (self.new_amount or 0) - (self.original_amount or 0)
