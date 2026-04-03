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
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Distribution"),
			"fieldname": "distribution",
			"fieldtype": "Link",
			"options": "Material Distribution",
			"width": 150,
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
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 90,
		},
		{
			"label": _("UOM"),
			"fieldname": "uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80,
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 120,
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
		conditions += " AND md.project = %(project)s"
	if filters.get("company"):
		conditions += " AND md.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND md.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND md.posting_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			md.posting_date,
			md.name AS distribution,
			md.project,
			md.task,
			mdi.item_code,
			mdi.item_name,
			mdi.qty,
			mdi.uom,
			mdi.rate,
			mdi.amount,
			mdi.budget_level_code
		FROM `tabMaterial Distribution` md
		INNER JOIN `tabMaterial Distribution Item` mdi
			ON mdi.parent = md.name AND mdi.parenttype = 'Material Distribution'
		WHERE md.docstatus = 1
			{conditions}
		ORDER BY md.posting_date DESC, md.name
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
