# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate


def check_authorization(doc, method):
	"""Check if a Purchase Invoice has been authorized before submission.

	Called via doc_events hook on Purchase Invoice on_submit.
	If an authorized Invoice Authorization exists, submission proceeds.
	Otherwise, a pending authorization request is auto-created and submission is blocked.
	"""
	# Check for an existing authorized record
	authorized = frappe.db.exists(
		"Invoice Authorization",
		{
			"purchase_invoice": doc.name,
			"status": "Authorized",
			"docstatus": 1,
		},
	)

	if authorized:
		return

	# No authorization found -- auto-create a pending one and block submission
	auth_doc = frappe.new_doc("Invoice Authorization")
	auth_doc.purchase_invoice = doc.name
	auth_doc.supplier = doc.supplier
	auth_doc.invoice_amount = doc.grand_total or doc.total
	auth_doc.requested_by = frappe.session.user
	auth_doc.request_date = nowdate()
	auth_doc.status = "Pending"
	auth_doc.company = doc.company
	auth_doc.comments = _(
		"Auto-created: authorization required before invoice submission"
	)
	auth_doc.insert(ignore_permissions=True)

	frappe.throw(
		_(
			"Purchase Invoice {0} requires authorization before submission. "
			"An Invoice Authorization request ({1}) has been created. "
			"Please get it authorized and then re-submit."
		).format(doc.name, auth_doc.name)
	)
