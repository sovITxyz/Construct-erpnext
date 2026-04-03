import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ProjectInvoice(Document):
	def validate(self):
		self.compute_total()

	def compute_total(self):
		total = 0
		for row in self.revenue_items or []:
			total += flt(row.amount)
		self.total_invoice_amount = total

	def on_submit(self):
		"""Create and submit a Sales Invoice from this Project Invoice."""
		si = frappe.new_doc("Sales Invoice")
		si.customer = self.customer
		si.posting_date = self.invoice_date
		si.company = self.company
		si.project = self.project

		income_account = frappe.db.get_value(
			"Company", self.company, "default_income_account"
		)
		if not income_account:
			frappe.throw(
				_("Please set a Default Income Account in company {0} settings.").format(
					self.company
				)
			)

		for row in self.revenue_items or []:
			si.append("items", {
				"item_name": row.description or _("Project Revenue"),
				"description": row.description or _("Project Revenue"),
				"qty": 1,
				"rate": flt(row.amount),
				"income_account": income_account,
			})

		si.flags.ignore_mandatory = True
		si.insert(ignore_permissions=True)
		si.submit()

		self.db_set("sales_invoice", si.name)

	def on_cancel(self):
		"""Cancel the linked Sales Invoice if it exists."""
		if self.sales_invoice:
			si = frappe.get_doc("Sales Invoice", self.sales_invoice)
			if si.docstatus == 1:
				si.cancel()
