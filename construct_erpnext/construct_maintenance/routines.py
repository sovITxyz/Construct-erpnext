# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, add_days, getdate


def check_preventive_schedules():
	"""Daily scheduler job: check for overdue preventive maintenance routines
	and create notifications or ToDos for responsible parties."""

	overdue_routines = frappe.get_all(
		"Maintenance Routine",
		filters={
			"active": 1,
			"routine_type": "Preventive",
			"next_due": ["<=", today()],
		},
		fields=["name", "routine_name", "asset", "next_due", "frequency", "company"],
	)

	for routine in overdue_routines:
		# Check if a notification was already sent today
		existing = frappe.db.exists(
			"ToDo",
			{
				"reference_type": "Maintenance Routine",
				"reference_name": routine.name,
				"date": today(),
			},
		)
		if existing:
			continue

		frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": (
					f"Preventive maintenance routine <b>{routine.routine_name}</b> "
					f"for asset <b>{routine.asset or 'N/A'}</b> is overdue. "
					f"Scheduled date: {routine.next_due}"
				),
				"reference_type": "Maintenance Routine",
				"reference_name": routine.name,
				"date": today(),
			}
		).insert(ignore_permissions=True)
