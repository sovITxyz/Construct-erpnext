# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate
from frappe.model.document import Document


class InvoiceAuthorization(Document):
	def validate(self):
		if not self.request_date:
			self.request_date = nowdate()

		if not self.requested_by:
			self.requested_by = frappe.session.user

	def on_submit(self):
		self.db_set("status", "Authorized")
		self.db_set("authorized_by", frappe.session.user)
		self.db_set("authorization_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Rejected")
