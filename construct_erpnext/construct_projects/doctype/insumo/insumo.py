import frappe
from frappe import _
from frappe.model.document import Document


class Insumo(Document):
	def validate(self):
		self.validate_formula()

	def validate_formula(self):
		if self.insumo_type in ("Compound", "Calculated") and not self.formula:
			frappe.throw(
				_("Formula is required for {0} type Insumos.").format(self.insumo_type)
			)
