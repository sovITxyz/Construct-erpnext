import frappe
from frappe.utils import flt


def get_budget_summary(project):
	"""Return a summary dict of the active/frozen budget for a project.

	Returns dict with keys: total_estimated, total_real, variance_amount, variance_pct
	or empty dict if no submitted budget exists.
	"""
	budget = frappe.db.get_value(
		"Construction Budget",
		{"project": project, "docstatus": 1},
		["total_estimated_amount", "total_real_cost", "variance_amount", "variance_pct"],
		as_dict=True,
		order_by="creation desc",
	)

	if not budget:
		return {}

	return {
		"total_estimated": flt(budget.total_estimated_amount),
		"total_real": flt(budget.total_real_cost),
		"variance_amount": flt(budget.variance_amount),
		"variance_pct": flt(budget.variance_pct),
	}


def get_advancement_pct(project):
	"""Return the latest real advancement percentage for a project.

	Returns float (0-100) or 0.0 if no submitted advancement exists.
	"""
	advancement = frappe.db.get_value(
		"Physical Advancement",
		{"project": project, "advancement_type": "Real", "docstatus": 1},
		"advancement_pct",
		order_by="period_date desc, creation desc",
	)

	return flt(advancement) if advancement else 0.0
