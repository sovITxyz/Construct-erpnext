# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, today


def distribute_costs(doc, method):
	"""Distribute salary slip costs to projects, equipment, and departments.

	Called via doc_events hook on Salary Slip on_submit.
	Creates a Payroll Cost Distribution if one does not already exist for this
	salary slip, using the employee's recent timesheet project allocations as
	the distribution basis.  Falls back to a single 100% allocation to the
	employee's default project when no timesheets are found.
	"""
	if frappe.db.exists(
		"Payroll Cost Distribution",
		{"salary_slip": doc.name, "docstatus": ["!=", 2]},
	):
		return

	gross_pay = flt(doc.gross_pay)
	if not gross_pay:
		return

	distribution_items = _build_distribution_items(doc)
	if not distribution_items:
		return

	pcd = frappe.get_doc(
		{
			"doctype": "Payroll Cost Distribution",
			"salary_slip": doc.name,
			"employee": doc.employee,
			"employee_name": doc.employee_name,
			"total_amount": gross_pay,
			"company": doc.company,
			"distribution_items": distribution_items,
		}
	)
	pcd.insert(ignore_permissions=True)
	pcd.submit()


def _build_distribution_items(doc):
	"""Derive distribution items from timesheet hours or employee default project."""
	items = _items_from_timesheets(doc)
	if items:
		return items

	default_project = frappe.db.get_value("Employee", doc.employee, "project")
	if default_project:
		return [
			{
				"target_type": "Project",
				"target_doctype": "Project",
				"target_name": default_project,
				"percentage": 100.0,
			}
		]

	return []


def _items_from_timesheets(doc):
	"""Build proportional distribution from timesheets in the salary period."""
	if not (doc.start_date and doc.end_date):
		return []

	rows = frappe.db.sql(
		"""
		SELECT tsd.project, SUM(tsd.hours) AS total_hours
		FROM `tabTimesheet Detail` tsd
		JOIN `tabTimesheet` ts ON ts.name = tsd.parent
		WHERE ts.employee = %(employee)s
		  AND ts.docstatus = 1
		  AND tsd.from_time >= %(start)s
		  AND tsd.to_time <= %(end)s
		  AND tsd.project IS NOT NULL
		  AND tsd.project != ''
		GROUP BY tsd.project
		""",
		{"employee": doc.employee, "start": doc.start_date, "end": doc.end_date},
		as_dict=True,
	)

	if not rows:
		return []

	grand_total_hours = sum(flt(r.total_hours) for r in rows)
	if not grand_total_hours:
		return []

	items = []
	for row in rows:
		pct = flt(row.total_hours) / grand_total_hours * 100
		items.append(
			{
				"target_type": "Project",
				"target_doctype": "Project",
				"target_name": row.project,
				"percentage": flt(pct, 2),
			}
		)

	# Adjust rounding so percentages sum to exactly 100
	total_pct = sum(i["percentage"] for i in items)
	if items and abs(total_pct - 100.0) > 0.001:
		items[-1]["percentage"] = flt(items[-1]["percentage"] + (100.0 - total_pct), 2)

	return items
