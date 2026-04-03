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
			"label": _("Budget"),
			"fieldname": "budget",
			"fieldtype": "Link",
			"options": "Construction Budget",
			"width": 150,
		},
		{
			"label": _("Level Code"),
			"fieldname": "level_code",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Level Name"),
			"fieldname": "level_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Level Type"),
			"fieldname": "level_type",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Estimated Total"),
			"fieldname": "estimated_total",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Real Total"),
			"fieldname": "real_total",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Variance"),
			"fieldname": "variance",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Variance %"),
			"fieldname": "variance_pct",
			"fieldtype": "Percent",
			"width": 110,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND cb.project = %(project)s"
	if filters.get("company"):
		conditions += " AND cb.company = %(company)s"

	date_conditions = ""
	if filters.get("from_date"):
		date_conditions += " AND pce.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		date_conditions += " AND pce.posting_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			cb.project,
			cb.name AS budget,
			bl.level_code,
			bl.level_name,
			bl.level_type,
			bl.estimated_total,
			IFNULL(pce_agg.actual_total, 0) AS real_total,
			bl.estimated_total - IFNULL(pce_agg.actual_total, 0) AS variance,
			CASE
				WHEN bl.estimated_total > 0
				THEN ROUND(((bl.estimated_total - IFNULL(pce_agg.actual_total, 0)) / bl.estimated_total) * 100, 2)
				ELSE 0
			END AS variance_pct
		FROM `tabConstruction Budget` cb
		INNER JOIN `tabBudget Level` bl ON bl.parent = cb.name AND bl.parenttype = 'Construction Budget'
		LEFT JOIN (
			SELECT
				pce.project,
				pce.budget_level_code,
				SUM(pce.amount) AS actual_total
			FROM `tabProject Cost Entry` pce
			WHERE pce.docstatus = 1
				{date_conditions}
			GROUP BY pce.project, pce.budget_level_code
		) pce_agg ON pce_agg.project = cb.project AND pce_agg.budget_level_code = bl.level_code
		WHERE cb.docstatus = 1
			{conditions}
		ORDER BY cb.project, bl.level_code
		""".format(
			conditions=conditions, date_conditions=date_conditions
		),
		filters,
		as_dict=True,
	)

	return data
