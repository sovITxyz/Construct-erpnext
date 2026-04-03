import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Insumo(Document):
	def validate(self):
		self.validate_formula()

	def validate_formula(self):
		if self.insumo_type in ("Compound", "Calculated") and not self.formula:
			frappe.throw(
				_("Formula is required for {0} type Insumos.").format(self.insumo_type)
			)

	def evaluate_price(self):
		"""Evaluate and set current_price based on insumo_type.

		- Simple: uses current_price as-is (no computation).
		- Compound: parses formula like "Cement:2 + Sand:3 + Gravel:4",
		  looks up each referenced Insumo's current_price, multiplies by qty, sums.
		- Calculated: replaces {Insumo Name} placeholders in formula with
		  their current_price values, then evaluates the expression.
		"""
		if self.insumo_type == "Simple":
			return flt(self.current_price)

		if self.insumo_type == "Compound":
			result = self._evaluate_compound()
		elif self.insumo_type == "Calculated":
			result = self._evaluate_calculated()
		else:
			frappe.throw(_("Unknown Insumo type: {0}").format(self.insumo_type))
			return

		self.current_price = flt(result)
		self.save()
		return self.current_price

	def _evaluate_compound(self):
		"""Parse 'Name:qty + Name:qty' formula, look up prices, sum products."""
		if not self.formula:
			frappe.throw(_("Formula is required for Compound Insumo."))

		total = 0.0
		parts = [p.strip() for p in self.formula.split("+")]

		for part in parts:
			if ":" not in part:
				frappe.throw(
					_("Invalid compound formula segment '{0}'. Expected 'Name:qty'.").format(part)
				)

			name, qty_str = part.rsplit(":", 1)
			name = name.strip()
			qty = flt(qty_str.strip())

			price = frappe.db.get_value("Insumo", {"insumo_name": name}, "current_price")
			if price is None:
				frappe.throw(_("Insumo '{0}' not found.").format(name))

			total += flt(price) * qty

		return total

	def _evaluate_calculated(self):
		"""Replace {Insumo Name} placeholders with prices and safe-eval the expression."""
		if not self.formula:
			frappe.throw(_("Formula is required for Calculated Insumo."))

		expression = self.formula
		references = re.findall(r"\{([^}]+)\}", expression)

		for ref_name in references:
			price = frappe.db.get_value("Insumo", {"insumo_name": ref_name}, "current_price")
			if price is None:
				frappe.throw(_("Insumo '{0}' not found.").format(ref_name))
			expression = expression.replace("{" + ref_name + "}", str(flt(price)))

		try:
			result = frappe.safe_eval(expression)
		except Exception as e:
			frappe.throw(_("Error evaluating formula: {0}").format(str(e)))

		return flt(result)


@frappe.whitelist()
def recalculate_insumo_price(insumo_name):
	"""Recalculate and persist the current_price for the given Insumo."""
	frappe.has_permission("Insumo", ptype="write", throw=True)

	doc = frappe.get_doc("Insumo", insumo_name)
	return doc.evaluate_price()
