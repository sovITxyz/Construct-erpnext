# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, flt
from frappe.model.document import Document

_ALLOWED_STATUSES = {"Requested", "Approved", "Printed", "Delivered", "Cancelled"}


class CheckRequest(Document):
	def validate(self):
		if self.status and self.status not in _ALLOWED_STATUSES:
			frappe.throw(
				_("Invalid status {0}. Must be one of: {1}").format(
					self.status, ", ".join(sorted(_ALLOWED_STATUSES))
				)
			)

		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))

		if not self.supplier:
			frappe.throw(_("Supplier is required"))

		if not self.purchase_invoice:
			frappe.throw(_("Purchase Invoice is required"))

	def before_submit(self):
		if not self.status:
			self.status = "Requested"

		if not self.requested_by:
			self.requested_by = frappe.session.user

		if not self.request_date:
			self.request_date = nowdate()
