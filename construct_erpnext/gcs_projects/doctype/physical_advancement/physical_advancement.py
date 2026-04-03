import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PhysicalAdvancement(Document):
	def validate(self):
		self.validate_advancement_pct()

	def validate_advancement_pct(self):
		if flt(self.advancement_pct) < 0:
			frappe.throw(_("Advancement % cannot be negative."))
		if flt(self.advancement_pct) > 100:
			frappe.throw(_("Advancement % cannot exceed 100."))

	def on_submit(self):
		self.update_project_progress()

	def update_project_progress(self):
		"""Update project percent_complete based on latest Real advancement."""
		if self.advancement_type == "Real" and self.project:
			frappe.db.set_value(
				"Project", self.project, "percent_complete", flt(self.advancement_pct)
			)
