# Copyright (c) 2026, SovIT and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


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
			"label": _("Cost Type"),
			"fieldname": "cost_type",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("% of Total"),
			"fieldname": "percentage_of_total",
			"fieldtype": "Percent",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND pce.project = %(project)s"
	if filters.get("company"):
		conditions += " AND pce.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND pce.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND pce.posting_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			pce.project,
			pce.cost_type,
			SUM(pce.amount) AS total_amount
		FROM `tabProject Cost Entry` pce
		WHERE pce.docstatus = 1
			{conditions}
		GROUP BY pce.project, pce.cost_type
		ORDER BY pce.project, total_amount DESC
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	# Calculate percentage of total per project
	project_totals = {}
	for row in data:
		project_totals.setdefault(row.project, 0)
		project_totals[row.project] += flt(row.total_amount)

	for row in data:
		project_total = flt(project_totals.get(row.project))
		if project_total > 0:
			row["percentage_of_total"] = round(
				(flt(row.total_amount) / project_total) * 100, 2
			)
		else:
			row["percentage_of_total"] = 0

	return data
