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
			"label": _("Change Order"),
			"fieldname": "change_order",
			"fieldtype": "Link",
			"options": "Budget Change Order",
			"width": 160,
		},
		{
			"label": _("Change Order Title"),
			"fieldname": "change_order_title",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Request Date"),
			"fieldname": "request_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Approval Date"),
			"fieldname": "approval_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Requested By"),
			"fieldname": "requested_by",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Level Name"),
			"fieldname": "level_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Budget Level Code"),
			"fieldname": "budget_level_code",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Change Type"),
			"fieldname": "change_type",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Original Amount"),
			"fieldname": "original_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("New Amount"),
			"fieldname": "new_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Change Amount"),
			"fieldname": "change_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND bco.project = %(project)s"
	if filters.get("company"):
		conditions += " AND bco.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND bco.request_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND bco.request_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			bco.project,
			bco.name AS change_order,
			bco.change_order_title,
			bco.request_date,
			bco.approval_date,
			bco.requested_by,
			bci.level_name,
			bci.budget_level_code,
			bci.change_type,
			bci.original_amount,
			bci.new_amount,
			bci.change_amount
		FROM `tabBudget Change Order` bco
		INNER JOIN `tabBudget Change Order Item` bci
			ON bci.parent = bco.name AND bci.parenttype = 'Budget Change Order'
		WHERE bco.docstatus = 1
			{conditions}
		ORDER BY bco.request_date DESC, bco.name
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
