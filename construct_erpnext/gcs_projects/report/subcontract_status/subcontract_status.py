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
			"label": _("Subcontract"),
			"fieldname": "subcontract",
			"fieldtype": "Link",
			"options": "Subcontract",
			"width": 150,
		},
		{
			"label": _("Contractor"),
			"fieldname": "contractor",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 130,
		},
		{
			"label": _("Contractor Name"),
			"fieldname": "contractor_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Contract Title"),
			"fieldname": "contract_title",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Status"),
			"fieldname": "contract_status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Negotiated Amount"),
			"fieldname": "negotiated_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Paid Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Remaining Amount"),
			"fieldname": "remaining_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 110,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND sc.project = %(project)s"
	if filters.get("company"):
		conditions += " AND sc.company = %(company)s"
	if filters.get("contractor"):
		conditions += " AND sc.contractor = %(contractor)s"
	if filters.get("status"):
		conditions += " AND sc.contract_status = %(status)s"

	data = frappe.db.sql(
		"""
		SELECT
			sc.project,
			sc.name AS subcontract,
			sc.contractor,
			sc.contractor_name,
			sc.contract_title,
			sc.contract_status,
			sc.negotiated_amount,
			sc.paid_amount,
			sc.remaining_amount,
			sc.start_date,
			sc.end_date
		FROM `tabSubcontract` sc
		WHERE sc.docstatus = 1
			{conditions}
		ORDER BY sc.project, sc.contractor_name
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
