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
			"label": _("Usage Date"),
			"fieldname": "usage_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Asset"),
			"fieldname": "asset",
			"fieldtype": "Link",
			"options": "Asset",
			"width": 140,
		},
		{
			"label": _("Asset Name"),
			"fieldname": "asset_name",
			"fieldtype": "Data",
			"width": 180,
		},
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
			"label": _("Hours Used"),
			"fieldname": "hours_used",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Cost Rate"),
			"fieldname": "cost_rate",
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
			"label": _("Budget Level Code"),
			"fieldname": "budget_level_code",
			"fieldtype": "Data",
			"width": 140,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND eul.project = %(project)s"
	if filters.get("asset"):
		conditions += " AND eul.asset = %(asset)s"
	if filters.get("company"):
		conditions += " AND eul.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND eul.usage_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND eul.usage_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			eul.usage_date,
			eul.asset,
			eul.asset_name,
			eul.project,
			eul.task,
			eul.hours_used,
			eul.cost_rate,
			eul.total_cost,
			eul.budget_level_code
		FROM `tabEquipment Usage Log` eul
		WHERE eul.docstatus = 1
			{conditions}
		ORDER BY eul.usage_date DESC, eul.asset
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
