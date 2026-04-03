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
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150,
		},
		{
			"label": _("Requested Qty"),
			"fieldname": "requested_qty",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Ordered Qty"),
			"fieldname": "ordered_qty",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Received Qty"),
			"fieldname": "received_qty",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Pending Qty"),
			"fieldname": "pending_qty",
			"fieldtype": "Float",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " AND mr.project = %(project)s"
	if filters.get("company"):
		conditions += " AND mr.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND mr.transaction_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND mr.transaction_date <= %(to_date)s"

	po_conditions = ""
	if filters.get("project"):
		po_conditions += " AND po.project = %(project)s"
	if filters.get("company"):
		po_conditions += " AND po.company = %(company)s"
	if filters.get("from_date"):
		po_conditions += " AND po.transaction_date >= %(from_date)s"
	if filters.get("to_date"):
		po_conditions += " AND po.transaction_date <= %(to_date)s"

	pr_conditions = ""
	if filters.get("project"):
		pr_conditions += " AND pr.project = %(project)s"
	if filters.get("company"):
		pr_conditions += " AND pr.company = %(company)s"
	if filters.get("from_date"):
		pr_conditions += " AND pr.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		pr_conditions += " AND pr.posting_date <= %(to_date)s"

	data = frappe.db.sql(
		"""
		SELECT
			items.item_code,
			items.item_name,
			items.project,
			IFNULL(items.requested_qty, 0) AS requested_qty,
			IFNULL(po_agg.ordered_qty, 0) AS ordered_qty,
			IFNULL(pr_agg.received_qty, 0) AS received_qty,
			IFNULL(items.requested_qty, 0) - IFNULL(pr_agg.received_qty, 0) AS pending_qty
		FROM (
			SELECT
				mri.item_code,
				mri.item_name,
				IFNULL(mri.project, mr.project) AS project,
				SUM(mri.qty) AS requested_qty
			FROM `tabMaterial Request Item` mri
			INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
			WHERE mr.docstatus = 1
				AND mr.material_request_type = 'Purchase'
				{conditions}
			GROUP BY mri.item_code, IFNULL(mri.project, mr.project)
		) items
		LEFT JOIN (
			SELECT
				poi.item_code,
				IFNULL(poi.project, po.project) AS project,
				SUM(poi.qty) AS ordered_qty
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
			WHERE po.docstatus = 1
				{po_conditions}
			GROUP BY poi.item_code, IFNULL(poi.project, po.project)
		) po_agg ON po_agg.item_code = items.item_code AND po_agg.project = items.project
		LEFT JOIN (
			SELECT
				pri.item_code,
				IFNULL(pri.project, pr.project) AS project,
				SUM(pri.qty) AS received_qty
			FROM `tabPurchase Receipt Item` pri
			INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
			WHERE pr.docstatus = 1
				{pr_conditions}
			GROUP BY pri.item_code, IFNULL(pri.project, pr.project)
		) pr_agg ON pr_agg.item_code = items.item_code AND pr_agg.project = items.project
		ORDER BY items.project, items.item_code
		""".format(
			conditions=conditions,
			po_conditions=po_conditions,
			pr_conditions=pr_conditions,
		),
		filters,
		as_dict=True,
	)

	return data
