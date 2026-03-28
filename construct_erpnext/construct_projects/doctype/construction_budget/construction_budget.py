import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class ConstructionBudget(Document):
	def validate(self):
		self.validate_budget_levels()
		self.compute_totals()

	def validate_budget_levels(self):
		if not self.budget_levels:
			frappe.throw(_("At least one Budget Level row is required."))

	def compute_totals(self):
		total_estimated = 0
		total_real = 0

		for row in self.budget_levels:
			row.estimated_total = flt(row.estimated_qty) * flt(row.estimated_unit_cost)
			row.variance = flt(row.estimated_total) - flt(row.real_total)
			total_estimated += flt(row.estimated_total)
			total_real += flt(row.real_total)

		self.total_estimated_amount = total_estimated
		self.total_real_cost = total_real
		self.variance_amount = total_estimated - total_real

		if total_estimated:
			self.variance_pct = (self.variance_amount / total_estimated) * 100
		else:
			self.variance_pct = 0

	def on_submit(self):
		if self.budget_status == "Draft":
			self.db_set("budget_status", "Frozen")
			self.db_set("frozen_date", nowdate())
			self.db_set("frozen_by", frappe.session.user)

	def on_cancel(self):
		self.db_set("budget_status", "Amended")
