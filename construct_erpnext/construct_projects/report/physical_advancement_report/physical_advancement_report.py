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
			"label": _("Period Date"),
			"fieldname": "period_date",
			"fieldtype": "Date",
			"width": 110,
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
			"label": _("Advancement %"),
			"fieldname": "advancement_pct",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Advancement Type"),
			"fieldname": "advancement_type",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Period Type"),
			"fieldname": "period_type",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND pa.project = %(project)s"
	if filters.get("advancement_type"):
		conditions += " AND pa.advancement_type = %(advancement_type)s"
	if filters.get("company"):
		conditions += " AND pa.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND pa.period_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND pa.period_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			pa.period_date,
			pa.project,
			pa.task,
			pa.advancement_pct,
			pa.advancement_type,
			pa.period_type,
			pa.company
		FROM `tabPhysical Advancement` pa
		WHERE pa.docstatus = 1
			{conditions}
		ORDER BY pa.period_date DESC, pa.project
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
