import frappe
from frappe.utils import flt


def update_project_progress(doc, method):
	"""Hook called on Physical Advancement submit to update the linked
	project's percent_complete field.

	Only updates if the advancement type is 'Real'.
	"""
	if doc.advancement_type != "Real":
		return

	if not doc.project:
		return

	frappe.db.set_value(
		"Project", doc.project, "percent_complete", flt(doc.advancement_pct)
	)
