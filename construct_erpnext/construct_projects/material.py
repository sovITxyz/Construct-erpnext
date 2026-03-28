import frappe
from frappe.utils import flt


def assign_cost_to_activity(doc, method):
	"""Hook called on Stock Entry submit to create Project Cost Entries
	for items linked to a project.

	Iterates over Stock Entry items and creates a Project Cost Entry
	for each item that has a project assigned.
	"""
	if not doc.items:
		return

	for item in doc.items:
		project = item.get("project") or doc.get("project")
		if not project:
			continue

		cost_entry = frappe.new_doc("Project Cost Entry")
		cost_entry.project = project
		cost_entry.cost_type = "Material"
		cost_entry.description = f"Stock Entry {doc.name} - {item.item_code}"
		cost_entry.amount = flt(item.amount) or (flt(item.qty) * flt(item.basic_rate))
		cost_entry.posting_date = doc.posting_date
		cost_entry.source_doctype = "Stock Entry"
		cost_entry.source_document = doc.name
		cost_entry.budget_level_code = item.get("budget_level_code") or ""
		cost_entry.company = doc.company
		cost_entry.insert(ignore_permissions=True)
		cost_entry.submit()
