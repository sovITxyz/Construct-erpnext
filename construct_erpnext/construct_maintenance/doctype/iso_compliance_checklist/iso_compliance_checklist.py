# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class ISOComplianceChecklist(Document):
	def validate(self):
		self._validate_evidence_for_compliant()
		self._calculate_next_review()

	def _validate_evidence_for_compliant(self):
		if self.compliance_status == "Compliant" and not self.evidence_document:
			frappe.throw(
				_("Evidence document is required for Compliant status.")
			)

	def _calculate_next_review(self):
		"""Auto-set next_review to one year after audit_date (annual review cycle)."""
		if self.audit_date:
			self.next_review = add_days(getdate(self.audit_date), 365)
