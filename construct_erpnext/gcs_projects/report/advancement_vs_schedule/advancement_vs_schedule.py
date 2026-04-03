# Copyright (c) 2026, SovIT and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, date_diff


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
			"label": _("Activity"),
			"fieldname": "activity_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Task"),
			"fieldname": "task",
			"fieldtype": "Link",
			"options": "Task",
			"width": 150,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Planned Start"),
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Planned End"),
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Duration (Days)"),
			"fieldname": "duration_days",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Actual Advancement %"),
			"fieldname": "actual_advancement_pct",
			"fieldtype": "Percent",
			"width": 160,
		},
		{
			"label": _("Planned %"),
			"fieldname": "planned_pct",
			"fieldtype": "Percent",
			"width": 110,
		},
		{
			"label": _("SPI"),
			"fieldname": "spi",
			"fieldtype": "Float",
			"precision": 3,
			"width": 100,
		},
		{
			"label": _("SPI Status"),
			"fieldname": "spi_status",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ""
	joins = ""
	if filters.get("project"):
		conditions += " AND asc_t.project = %(project)s"
	if filters.get("company"):
		joins += " INNER JOIN `tabProject` proj ON proj.name = asc_t.project"
		conditions += " AND proj.company = %(company)s"

	# Use a custom alias to avoid SQL reserved word conflicts
	activities = frappe.db.sql(
		"""
		SELECT
			asc_t.project,
			asc_t.activity_name,
			asc_t.task,
			asc_t.status,
			asc_t.start_date,
			asc_t.end_date,
			asc_t.duration_days,
			asc_t.physical_advancement_pct AS actual_advancement_pct
		FROM `tabActivity Schedule` asc_t
		{joins}
		WHERE asc_t.docstatus = 1
			{conditions}
		ORDER BY asc_t.project, asc_t.start_date
		""".format(
			joins=joins,
			conditions=conditions,
		),
		filters,
		as_dict=True,
	)

	current_date = getdate(today())

	for row in activities:
		# Calculate planned % based on elapsed time
		if row.start_date and row.end_date:
			total_days = date_diff(row.end_date, row.start_date)
			if total_days > 0:
				elapsed_days = date_diff(current_date, row.start_date)
				elapsed_days = max(0, min(elapsed_days, total_days))
				row["planned_pct"] = round((elapsed_days / total_days) * 100, 2)
			else:
				row["planned_pct"] = 100.0
		else:
			row["planned_pct"] = 0.0

		# Calculate SPI = actual_advancement / planned_advancement
		actual = row.get("actual_advancement_pct") or 0
		planned = row.get("planned_pct") or 0
		if planned > 0:
			row["spi"] = round(actual / planned, 3)
		else:
			row["spi"] = 0.0

		if planned == 0:
			row["spi_status"] = "N/A"
		elif row["spi"] >= 1:
			row["spi_status"] = "On/Ahead"
		else:
			row["spi_status"] = "Behind"

	return activities
