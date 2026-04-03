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
		self.apply_changes_to_budget()

	def apply_changes_to_budget(self):
		"""Apply change order items to the linked Construction Budget."""
		if not self.construction_budget:
			frappe.throw(_("Construction Budget is required to apply changes."))

		budget = frappe.get_doc("Construction Budget", self.construction_budget)
		budget.flags.ignore_validate_update_after_submit = True

		for item in self.change_items or []:
			change_type = item.change_type

			if change_type == "Add":
				budget.append("budget_levels", {
					"level_code": item.budget_level_code,
					"level_name": item.level_name,
					"estimated_total": flt(item.new_amount),
				})

			elif change_type == "Modify":
				matched = False
				for bl in budget.budget_levels:
					if bl.level_code == item.budget_level_code:
						# Derive unit cost from new_amount if qty exists, otherwise set total directly
						if flt(bl.estimated_qty):
							bl.estimated_unit_cost = flt(item.new_amount) / flt(bl.estimated_qty)
						else:
							bl.estimated_qty = 1
							bl.estimated_unit_cost = flt(item.new_amount)
						bl.estimated_total = flt(item.new_amount)
						matched = True
						break
				if not matched:
					frappe.throw(
						_("Budget Level with code '{0}' not found for modification.").format(
							item.budget_level_code
						)
					)

			elif change_type == "Remove":
				to_remove = None
				for bl in budget.budget_levels:
					if bl.level_code == item.budget_level_code:
						to_remove = bl
						break
				if to_remove:
					budget.remove(to_remove)
				else:
					frappe.throw(
						_("Budget Level with code '{0}' not found for removal.").format(
							item.budget_level_code
						)
					)

		budget.compute_totals()
		budget.save(ignore_permissions=True)
