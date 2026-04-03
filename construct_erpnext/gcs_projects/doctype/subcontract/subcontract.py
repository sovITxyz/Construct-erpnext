import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class Subcontract(Document):
	def validate(self):
		self.compute_remaining()
		self.validate_dates()

	def compute_remaining(self):
		self.remaining_amount = flt(self.negotiated_amount) - flt(self.paid_amount)

	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(_("End Date cannot be before Start Date."))

	def on_submit(self):
		if self.contract_status == "Draft":
			self.db_set("contract_status", "Authorized")
