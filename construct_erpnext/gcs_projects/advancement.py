import frappe
from frappe import _
from frappe.utils import flt


def update_project_progress(doc, method):
	"""Hook called on Physical Advancement submit to update project/task/subcontract
	progress based on advancement_type.

	- Real: update Project percent_complete and Task progress (if task is set).
	- Client Authorized: update the linked Project Revenue's invoiced tracking.
	- Subcontractor Authorized: update the matching Subcontract activity's authorized_pct.

	Also validates that progress cannot go backwards for the same project+type.
	"""
	if not doc.project:
		return

	_validate_no_regression(doc)

	advancement_type = doc.advancement_type

	if advancement_type == "Real":
		_handle_real_advancement(doc)
	elif advancement_type == "Client Authorized":
		_handle_client_authorized(doc)
	elif advancement_type == "Subcontractor Authorized":
		_handle_subcontractor_authorized(doc)


def _validate_no_regression(doc):
	"""Ensure the new advancement_pct is not less than the latest submitted value
	for the same project and advancement_type."""
	previous_pct = frappe.db.sql(
		"""
		SELECT advancement_pct
		FROM `tabPhysical Advancement`
		WHERE project = %s
			AND advancement_type = %s
			AND docstatus = 1
			AND name != %s
		ORDER BY period_date DESC, creation DESC
		LIMIT 1
		""",
		(doc.project, doc.advancement_type, doc.name),
		as_dict=True,
	)

	if previous_pct and flt(doc.advancement_pct) < flt(previous_pct[0].advancement_pct):
		frappe.throw(
			_("Advancement cannot go backwards. Current {0}% is less than previous {1}%.").format(
				flt(doc.advancement_pct), flt(previous_pct[0].advancement_pct)
			)
		)


def _handle_real_advancement(doc):
	"""Update Project percent_complete and Task progress for Real advancement."""
	frappe.db.set_value(
		"Project", doc.project, "percent_complete", flt(doc.advancement_pct)
	)

	if doc.task:
		frappe.db.set_value("Task", doc.task, "progress", flt(doc.advancement_pct))


def _handle_client_authorized(doc):
	"""Mark Project Revenue records as ready for billing based on advancement."""
	revenues = frappe.get_all(
		"Project Revenue",
		filters={"project": doc.project, "docstatus": 1},
		fields=["name", "negotiated_amount"],
		order_by="creation asc",
	)

	for rev in revenues:
		billable_amount = flt(rev.negotiated_amount) * flt(doc.advancement_pct) / 100
		frappe.db.set_value("Project Revenue", rev.name, "invoiced_amount", billable_amount)
		remaining = flt(rev.negotiated_amount) - billable_amount
		frappe.db.set_value("Project Revenue", rev.name, "remaining_amount", remaining)


def _handle_subcontractor_authorized(doc):
	"""Find the matching Subcontract for this project and update the
	matching activity's authorized_pct."""
	subcontracts = frappe.get_all(
		"Subcontract",
		filters={"project": doc.project, "docstatus": 1},
		fields=["name"],
	)

	if not subcontracts:
		return

	task_name = None
	if doc.task:
		task_name = frappe.db.get_value("Task", doc.task, "subject")

	for sc_ref in subcontracts:
		sc = frappe.get_doc("Subcontract", sc_ref.name)
		sc.flags.ignore_validate_update_after_submit = True
		updated = False

		for activity in sc.activities or []:
			# Match by task subject against activity_name
			if task_name and activity.activity_name == task_name:
				activity.authorized_pct = flt(doc.advancement_pct)
				updated = True
				break

		if updated:
			sc.save(ignore_permissions=True)
			break
