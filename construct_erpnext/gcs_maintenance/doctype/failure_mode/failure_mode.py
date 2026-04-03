# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FailureMode(Document):
	def validate(self):
		self.validate_ratings()
		self.compute_rpn_score()

	def validate_ratings(self):
		for field, label in [
			("severity", "Severity"),
			("occurrence_probability", "Occurrence Probability"),
			("detection_rating", "Detection Rating"),
		]:
			value = self.get(field) or 0
			if not (1 <= value <= 10):
				frappe.throw(f"{label} must be between 1 and 10.")

	def compute_rpn_score(self):
		self.rpn_score = (self.severity or 0) * (self.occurrence_probability or 0) * (self.detection_rating or 0)
