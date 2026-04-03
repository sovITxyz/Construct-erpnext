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


def get_project_cost_breakdown(project):
	"""Return Project Cost Entry totals grouped by cost_type.

	Returns a list of dicts: [{"cost_type": "Material", "total_amount": 50000.0}, ...]
	"""
	results = frappe.db.sql(
		"""
		SELECT cost_type, SUM(amount) AS total_amount
		FROM `tabProject Cost Entry`
		WHERE project = %s AND docstatus = 1
		GROUP BY cost_type
		ORDER BY total_amount DESC
		""",
		(project,),
		as_dict=True,
	)

	return [
		{"cost_type": r.cost_type, "total_amount": flt(r.total_amount)}
		for r in results
	]


def get_project_schedule_status(project):
	"""Return Activity Schedule counts grouped by status.

	Returns a dict: {"Not Started": 5, "In Progress": 3, "Completed": 2, "Delayed": 1}
	"""
	results = frappe.db.sql(
		"""
		SELECT status, COUNT(*) AS cnt
		FROM `tabActivity Schedule`
		WHERE project = %s
		GROUP BY status
		""",
		(project,),
		as_dict=True,
	)

	return {r.status: r.cnt for r in results}
