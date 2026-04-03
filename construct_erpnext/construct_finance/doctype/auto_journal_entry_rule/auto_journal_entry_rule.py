# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from frappe.model.document import Document


class AutoJournalEntryRule(Document):
	def validate(self):
		if not self.trigger_doctype:
			frappe.throw(_("Trigger DocType is required"))
		if not self.trigger_event:
			frappe.throw(_("Trigger Event is required"))
		if not self.debit_account:
			frappe.throw(_("Debit Account is required"))
		if not self.credit_account:
			frappe.throw(_("Credit Account is required"))
		if not self.amount_field:
			frappe.throw(_("Amount Field is required"))


def execute_auto_je_rules(doc, event):
	"""Execute all active Auto Journal Entry Rules that match the given document and event.

	This is called from doc_events or can be called programmatically.

	Args:
		doc: The document triggering the rules.
		event: The trigger event string (on_submit, on_cancel, on_update).
	"""
	rules = frappe.get_all(
		"Auto Journal Entry Rule",
		filters={
			"active": 1,
			"trigger_doctype": doc.doctype,
			"trigger_event": event,
			"company": doc.get("company") or "",
		},
		fields=["name", "debit_account", "credit_account", "amount_field", "description", "company"],
	)

	if not rules:
		return

	for rule in rules:
		amount = flt(doc.get(rule.amount_field))
		if amount <= 0:
			frappe.log_error(
				title=_("Auto JE Rule Skipped"),
				message=_("Rule {0}: amount field '{1}' is zero or negative on {2} {3}").format(
					rule.name, rule.amount_field, doc.doctype, doc.name
				),
			)
			continue

		company = rule.company or doc.get("company")
		if not company:
			frappe.log_error(
				title=_("Auto JE Rule Skipped"),
				message=_("Rule {0}: no company found on rule or document {1} {2}").format(
					rule.name, doc.doctype, doc.name
				),
			)
			continue

		je = frappe.new_doc("Journal Entry")
		je.posting_date = nowdate()
		je.company = company
		je.user_remark = rule.description or _(
			"Auto Journal Entry from {0}: {1}"
		).format(doc.doctype, doc.name)

		je.append("accounts", {
			"account": rule.debit_account,
			"debit_in_account_currency": amount,
			"credit_in_account_currency": 0,
			"reference_type": doc.doctype,
			"reference_name": doc.name,
		})

		je.append("accounts", {
			"account": rule.credit_account,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": amount,
			"reference_type": doc.doctype,
			"reference_name": doc.name,
		})

		je.insert(ignore_permissions=True)
		je.submit()
