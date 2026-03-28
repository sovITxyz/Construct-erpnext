import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class BudgetChangeOrder(Document):
	def validate(self):
		self.compute_change_totals()

	def compute_change_totals(self):
		total = 0
		for row in self.change_items or []:
			row.change_amount = flt(row.new_amount) - flt(row.original_amount)
			total += flt(row.change_amount)
		self.total_change_amount = total

	def on_submit(self):
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approval_date", nowdate())
