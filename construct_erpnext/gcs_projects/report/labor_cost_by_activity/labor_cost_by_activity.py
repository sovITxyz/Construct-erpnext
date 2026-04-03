# Copyright (c) 2026, SovIT and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150,
		},
		{
			"label": _("Task"),
			"fieldname": "task",
			"fieldtype": "Link",
			"options": "Task",
			"width": 150,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Hours"),
			"fieldname": "hours",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Total Cost"),
			"fieldname": "total_cost",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Crew Code"),
			"fieldname": "crew_code",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Budget Level Code"),
			"fieldname": "budget_level_code",
			"fieldtype": "Data",
			"width": 140,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND lhe.project = %(project)s"
	if filters.get("company"):
		conditions += " AND lhe.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND lhe.employee = %(employee)s"
	if filters.get("from_date"):
		conditions += " AND lhe.period_start >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND lhe.period_end <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			lhe.project,
			lhe.task,
			lhe.employee,
			lhe.employee_name,
			SUM(lhe.hours) AS hours,
			AVG(lhe.rate) AS rate,
			SUM(lhe.total_cost) AS total_cost,
			lhe.crew_code,
			lhe.budget_level_code
		FROM `tabLabor Hour Entry` lhe
		WHERE lhe.docstatus = 1
			{conditions}
		GROUP BY lhe.project, lhe.task, lhe.employee, lhe.crew_code, lhe.budget_level_code
		ORDER BY lhe.project, lhe.task, lhe.employee
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
