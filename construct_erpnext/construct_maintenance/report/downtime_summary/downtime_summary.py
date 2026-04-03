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
			"label": _("Asset"),
			"fieldname": "asset",
			"fieldtype": "Link",
			"options": "Asset",
			"width": 150,
		},
		{
			"label": _("Asset Name"),
			"fieldname": "asset_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Incident Count"),
			"fieldname": "incident_count",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Total Duration (Hours)"),
			"fieldname": "total_duration_hours",
			"fieldtype": "Float",
			"width": 170,
		},
		{
			"label": _("Total Cost Impact"),
			"fieldname": "total_cost_impact",
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " AND dr.company = %(company)s"
	if filters.get("asset"):
		conditions += " AND dr.asset = %(asset)s"
	if filters.get("from_date"):
		conditions += " AND dr.start_datetime >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND dr.end_datetime <= CONCAT(%(to_date)s, ' 23:59:59')"

	data = frappe.db.sql(
		"""
		SELECT
			dr.asset,
			dr.asset_name,
			COUNT(dr.name) AS incident_count,
			SUM(dr.duration_hours) AS total_duration_hours,
			SUM(dr.estimated_cost_impact) AS total_cost_impact
		FROM `tabDowntime Record` dr
		WHERE dr.docstatus = 1
			{conditions}
		GROUP BY dr.asset, dr.asset_name
		ORDER BY total_duration_hours DESC
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
