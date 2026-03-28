import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ProjectCostEntry(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero."))
