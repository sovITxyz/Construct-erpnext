# Copyright (c) 2026, SovIT and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Failure Mode"),
			"fieldname": "failure_mode_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Asset Category"),
			"fieldname": "asset_category",
			"fieldtype": "Link",
			"options": "Asset Category",
			"width": 150,
		},
		{
			"label": _("Severity"),
			"fieldname": "severity",
			"fieldtype": "Int",
			"width": 90,
		},
		{
			"label": _("Occurrence"),
			"fieldname": "occurrence_probability",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": _("Detection"),
			"fieldname": "detection_rating",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("RPN Score"),
			"fieldname": "rpn_score",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": _("Recommended Action"),
			"fieldname": "recommended_action",
			"fieldtype": "Data",
			"width": 300,
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("asset_category"):
		conditions += " AND fm.asset_category = %(asset_category)s"
	if filters.get("min_rpn"):
		conditions += " AND fm.rpn_score >= %(min_rpn)s"

	data = frappe.db.sql(
		"""
		SELECT
			fm.failure_mode_name,
			fm.asset_category,
			fm.severity,
			fm.occurrence_probability,
			fm.detection_rating,
			fm.rpn_score,
			fm.recommended_action
		FROM `tabFailure Mode` fm
		WHERE 1=1
			{conditions}
		ORDER BY fm.rpn_score DESC
		""".format(
			conditions=conditions
		),
		filters,
		as_dict=True,
	)

	return data
