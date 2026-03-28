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
			"label": _("Downtime Cost"),
			"fieldname": "downtime_cost",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Parts Cost"),
			"fieldname": "parts_cost",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Total Cost"),
			"fieldname": "total_cost",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters):
	conditions_dt = ""
	conditions_mr = ""
	if filters.get("company"):
		conditions_dt += " AND dr.company = %(company)s"
		conditions_mr += " AND mr.company = %(company)s"
	if filters.get("asset"):
		conditions_dt += " AND dr.asset = %(asset)s"
		conditions_mr += " AND mr.asset = %(asset)s"
	if filters.get("from_date"):
		conditions_dt += " AND dr.start_datetime >= %(from_date)s"
	if filters.get("to_date"):
		conditions_dt += " AND dr.end_datetime <= CONCAT(%(to_date)s, ' 23:59:59')"

	# Get downtime costs grouped by asset
	downtime_data = frappe.db.sql(
		"""
		SELECT
			dr.asset,
			dr.asset_name,
			SUM(dr.estimated_cost_impact) AS downtime_cost
		FROM `tabDowntime Record` dr
		WHERE dr.docstatus = 1
			{conditions}
		GROUP BY dr.asset, dr.asset_name
		""".format(
			conditions=conditions_dt
		),
		filters,
		as_dict=True,
	)

	# Get spare parts cost from maintenance routines
	# Since Maintenance Spare Part has no rate, join with Item valuation_rate
	parts_data = frappe.db.sql(
		"""
		SELECT
			mr.asset,
			SUM(msp.qty * IFNULL(item.valuation_rate, 0)) AS parts_cost
		FROM `tabMaintenance Routine` mr
		INNER JOIN `tabMaintenance Spare Part` msp
			ON msp.parent = mr.name AND msp.parenttype = 'Maintenance Routine'
		LEFT JOIN `tabItem` item ON item.name = msp.item_code
		WHERE mr.active = 1
			{conditions}
		GROUP BY mr.asset
		""".format(
			conditions=conditions_mr
		),
		filters,
		as_dict=True,
	)

	parts_map = {}
	for row in parts_data:
		if row.asset:
			parts_map[row.asset] = flt(row.parts_cost)

	# Build combined result
	asset_map = {}
	for row in downtime_data:
		asset_map[row.asset] = {
			"asset": row.asset,
			"asset_name": row.asset_name,
			"downtime_cost": flt(row.downtime_cost),
			"parts_cost": flt(parts_map.get(row.asset, 0)),
		}

	# Add assets that have parts cost but no downtime records
	for asset, parts_cost in parts_map.items():
		if asset not in asset_map:
			asset_name = frappe.db.get_value("Asset", asset, "asset_name") or ""
			asset_map[asset] = {
				"asset": asset,
				"asset_name": asset_name,
				"downtime_cost": 0,
				"parts_cost": flt(parts_cost),
			}

	data = []
	for asset in sorted(asset_map.keys()):
		row = asset_map[asset]
		row["total_cost"] = flt(row["downtime_cost"]) + flt(row["parts_cost"])
		data.append(row)

	return data
