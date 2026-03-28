# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, get_url_to_form


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

		# Send email notifications to Maintenance Engineer role users
		_notify_maintenance_engineers(routine)


def _notify_maintenance_engineers(routine):
	"""Send an email notification about an overdue routine to all users with
	the Maintenance Engineer role within the routine's company."""

	recipients = _get_maintenance_engineers(routine.company)
	if not recipients:
		return

	asset_label = routine.asset or "N/A"
	routine_url = get_url_to_form("Maintenance Routine", routine.name)
	subject = _("Overdue Maintenance: {0} for {1}").format(
		routine.routine_name, asset_label
	)
	message = _(
		"<p>The preventive maintenance routine <b>{routine_name}</b> "
		"for asset <b>{asset}</b> is overdue.</p>"
		"<p><b>Scheduled date:</b> {next_due}<br>"
		"<b>Frequency:</b> {frequency}</p>"
		'<p><a href="{url}">View Maintenance Routine</a></p>'
	).format(
		routine_name=routine.routine_name,
		asset=asset_label,
		next_due=routine.next_due,
		frequency=routine.frequency,
		url=routine_url,
	)

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype="Maintenance Routine",
			reference_name=routine.name,
		)
	except Exception:
		frappe.log_error(
			title=_("Maintenance Email Failed"),
			message=frappe.get_traceback(),
		)


def _get_maintenance_engineers(company):
	"""Return email addresses of users with 'Maintenance Engineer' role
	who belong to the given company (or have no company restriction)."""

	users = frappe.get_all(
		"Has Role",
		filters={"role": "Maintenance Engineer", "parenttype": "User"},
		fields=["parent"],
	)

	if not users:
		return []

	user_emails = list({u.parent for u in users})

	# Filter to enabled users only
	enabled = frappe.get_all(
		"User",
		filters={"name": ["in", user_emails], "enabled": 1},
		pluck="name",
	)

	return enabled
