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

	def update_real_costs(self):
		"""Query submitted Project Cost Entries for this project, grouped by
		budget_level_code, and update each Budget Level's real cost fields."""
		if not self.project:
			return

		actuals = frappe.db.sql(
			"""
			SELECT
				budget_level_code,
				SUM(amount) AS total_amount,
				COUNT(*) AS entry_count
			FROM `tabProject Cost Entry`
			WHERE project = %s
				AND docstatus = 1
				AND IFNULL(budget_level_code, '') != ''
			GROUP BY budget_level_code
			""",
			(self.project,),
			as_dict=True,
		)

		# Build lookup: budget_level_code -> aggregated values
		actuals_map = {}
		for row in actuals:
			actuals_map[row.budget_level_code] = row

		for bl in self.budget_levels:
			actual = actuals_map.get(bl.level_code)
			if actual:
				bl.real_total = flt(actual.total_amount)
				bl.real_qty = flt(actual.entry_count)
				bl.real_unit_cost = (
					flt(bl.real_total) / flt(bl.real_qty) if flt(bl.real_qty) else 0
				)
			else:
				bl.real_total = 0
				bl.real_qty = 0
				bl.real_unit_cost = 0

		self.compute_totals()


@frappe.whitelist()
def refresh_budget_actuals(budget_name):
	"""Load a Construction Budget, refresh real costs from Project Cost Entries, and save."""
	frappe.has_permission("Construction Budget", ptype="write", throw=True)

	budget = frappe.get_doc("Construction Budget", budget_name)
	budget.flags.ignore_validate_update_after_submit = True
	budget.update_real_costs()
	budget.save(ignore_permissions=True)

	return {"message": "Budget actuals refreshed successfully."}
