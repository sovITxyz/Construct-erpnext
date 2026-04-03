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
			"width": 180,
		},
		{
			"label": _("Advancement %"),
			"fieldname": "advancement_pct",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Total Estimated"),
			"fieldname": "total_estimated",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Total Real Cost"),
			"fieldname": "total_real_cost",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Budget Consumed %"),
			"fieldname": "budget_consumed_pct",
			"fieldtype": "Percent",
			"width": 150,
		},
		{
			"label": _("CPI"),
			"fieldname": "cpi",
			"fieldtype": "Float",
			"precision": 3,
			"width": 100,
		},
		{
			"label": _("CPI Status"),
			"fieldname": "cpi_status",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND cb.project = %(project)s"
	if filters.get("company"):
		conditions += " AND cb.company = %(company)s"

	data = frappe.db.sql(
		"""
		SELECT
			cb.project,
			IFNULL(pa_agg.advancement_pct, 0) AS advancement_pct,
			cb.total_estimated_amount AS total_estimated,
			IFNULL(pce_agg.total_real_cost, 0) AS total_real_cost,
			CASE
				WHEN cb.total_estimated_amount > 0
				THEN ROUND((IFNULL(pce_agg.total_real_cost, 0) / cb.total_estimated_amount) * 100, 2)
				ELSE 0
			END AS budget_consumed_pct,
			CASE
				WHEN IFNULL(pce_agg.total_real_cost, 0) > 0 AND cb.total_estimated_amount > 0
				THEN ROUND(
					(IFNULL(pa_agg.advancement_pct, 0) / 100)
					/ (IFNULL(pce_agg.total_real_cost, 0) / cb.total_estimated_amount),
					3
				)
				ELSE 0
			END AS cpi,
			CASE
				WHEN IFNULL(pce_agg.total_real_cost, 0) = 0 OR cb.total_estimated_amount = 0
				THEN 'N/A'
				WHEN (IFNULL(pa_agg.advancement_pct, 0) / 100)
					/ (IFNULL(pce_agg.total_real_cost, 0) / cb.total_estimated_amount) >= 1
				THEN 'On/Under Budget'
				ELSE 'Over Budget'
			END AS cpi_status
		FROM `tabConstruction Budget` cb
		LEFT JOIN (
			SELECT
				pa.project,
				MAX(pa.advancement_pct) AS advancement_pct
			FROM `tabPhysical Advancement` pa
			WHERE pa.docstatus = 1
				AND pa.advancement_type = 'Real'
			GROUP BY pa.project
		) pa_agg ON pa_agg.project = cb.project
		LEFT JOIN (
			SELECT
				pce.project,
				SUM(pce.amount) AS total_real_cost
			FROM `tabProject Cost Entry` pce
			WHERE pce.docstatus = 1
			GROUP BY pce.project
		) pce_agg ON pce_agg.project = cb.project
		WHERE cb.docstatus = 1
			{conditions}
		ORDER BY cb.project
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
