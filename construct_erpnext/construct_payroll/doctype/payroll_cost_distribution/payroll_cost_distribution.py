# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class PayrollCostDistribution(Document):
	def validate(self):
		self._validate_items_exist()
		self._validate_percentages()
		self._compute_amounts()

	def on_submit(self):
		self._create_project_cost_entries()

	def on_cancel(self):
		self._cancel_linked_cost_entries()

	# --- validation helpers ---

	def _validate_items_exist(self):
		if not self.distribution_items:
			frappe.throw(_("At least one Distribution Item is required."))

	def _validate_percentages(self):
		total_pct = sum(flt(item.percentage) for item in self.distribution_items)
		if abs(total_pct - 100.0) > 0.01:
			frappe.throw(
				_("Distribution percentages must sum to 100%. Currently: {0}%").format(
					flt(total_pct, 2)
				)
			)

	def _compute_amounts(self):
		for item in self.distribution_items:
			item.amount = flt(
				flt(self.total_amount) * flt(item.percentage) / 100.0, 2
			)

	# --- submit / cancel helpers ---

	def _create_project_cost_entries(self):
		for item in self.distribution_items:
			if item.target_type != "Project":
				continue

			pce = frappe.get_doc(
				{
					"doctype": "Project Cost Entry",
					"project": item.target_name,
					"cost_type": "Labor",
					"amount": flt(item.amount),
					"posting_date": today(),
					"company": self.company,
					"description": _("Labor cost from Salary Slip {0} for {1}").format(
						self.salary_slip, self.employee_name or self.employee
					),
					"source_doctype": "Payroll Cost Distribution",
					"source_document": self.name,
				}
			)
			pce.insert(ignore_permissions=True)
			pce.submit()

	def _cancel_linked_cost_entries(self):
		linked = frappe.get_all(
			"Project Cost Entry",
			filters={
				"source_doctype": "Payroll Cost Distribution",
				"source_document": self.name,
				"docstatus": 1,
			},
			pluck="name",
		)
		for pce_name in linked:
			pce = frappe.get_doc("Project Cost Entry", pce_name)
			pce.cancel()
