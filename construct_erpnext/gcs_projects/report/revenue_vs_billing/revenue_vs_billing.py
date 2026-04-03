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
			"label": _("Revenue Name"),
			"fieldname": "revenue_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Revenue Type"),
			"fieldname": "revenue_type",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{
			"label": _("Negotiated Amount"),
			"fieldname": "negotiated_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Invoiced Amount"),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Remaining Amount"),
			"fieldname": "remaining_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Billing %"),
			"fieldname": "billing_pct",
			"fieldtype": "Percent",
			"width": 110,
		},
		{
			"label": _("Expected Date"),
			"fieldname": "expected_date",
			"fieldtype": "Date",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND pr.project = %(project)s"
	if filters.get("customer"):
		conditions += " AND pr.customer = %(customer)s"
	if filters.get("company"):
		conditions += " AND pr.company = %(company)s"

	data = frappe.db.sql(
		"""
		SELECT
			pr.project,
			pr.revenue_name,
			pr.revenue_type,
			pr.customer,
			pr.negotiated_amount,
			pr.invoiced_amount,
			pr.remaining_amount,
			CASE
				WHEN pr.negotiated_amount > 0
				THEN ROUND((pr.invoiced_amount / pr.negotiated_amount) * 100, 2)
				ELSE 0
			END AS billing_pct,
			pr.expected_date
		FROM `tabProject Revenue` pr
		WHERE pr.docstatus = 1
			{conditions}
		ORDER BY pr.project, pr.revenue_name
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
