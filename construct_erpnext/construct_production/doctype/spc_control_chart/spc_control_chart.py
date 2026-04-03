# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class SPCControlChart(Document):
	def validate(self):
		self.validate_control_limits()
		self.evaluate_data_points()

	def validate_control_limits(self):
		if self.lower_control_limit >= self.upper_control_limit:
			frappe.throw(_("Lower Control Limit must be less than Upper Control Limit."))
		if not (self.lower_control_limit <= self.center_line <= self.upper_control_limit):
			frappe.throw(_("Center Line must be between Lower and Upper Control Limits."))

	def evaluate_data_points(self):
		"""Mark each data point as in-control or out-of-control."""
		all_in_control = True
		for row in self.data_points:
			row.in_control = int(
				self.lower_control_limit <= row.measured_value <= self.upper_control_limit
			)
			if not row.in_control:
				all_in_control = False

		if self.data_points:
			if all_in_control:
				self.status = "In Control"
			else:
				self.status = "Out of Control"

	@frappe.whitelist()
	def add_data_point(self, value):
		"""Append a new data point, evaluate it, and trigger corrective action
		if the chart goes out of control."""
		value = flt(value)
		sample_number = len(self.data_points) + 1

		self.append(
			"data_points",
			{
				"measured_value": value,
				"sample_date": now_datetime(),
				"sample_number": sample_number,
			},
		)

		self.evaluate_data_points()
		self.save(ignore_permissions=True)

		if self.status == "Out of Control":
			self._trigger_corrective_action()

	def _trigger_corrective_action(self):
		"""Create a Corrective Action Tracker when the chart is out of control."""
		# Avoid creating duplicate open actions for the same chart
		existing = frappe.db.exists(
			"Corrective Action Tracker",
			{
				"methodology": "SPC",
				"work_order": self.work_order or "",
				"status": ["in", ["Open", "In Progress", "Containment", "Root Cause Analysis"]],
				"docstatus": ["!=", 2],
			},
		)
		if existing:
			return

		company = frappe.db.get_value("Work Order", self.work_order, "company") if self.work_order else None
		if not company:
			company = frappe.defaults.get_defaults().get("company") or frappe.db.get_single_value(
				"Global Defaults", "default_company"
			)

		ooc_values = [
			row.measured_value
			for row in self.data_points
			if not row.in_control
		]
		ooc_summary = ", ".join(str(v) for v in ooc_values[-5:])  # last 5 for brevity

		cat = frappe.get_doc(
			{
				"doctype": "Corrective Action Tracker",
				"title": _("SPC Out of Control: {0}").format(self.chart_name),
				"methodology": "SPC",
				"status": "Open",
				"priority": "High",
				"work_order": self.work_order,
				"company": company,
				"problem_statement": _(
					"<p>SPC Control Chart <b>{chart}</b> (process: {process}, "
					"measurement: {measurement}) has gone out of control.</p>"
					"<p>UCL: {ucl}, CL: {cl}, LCL: {lcl}</p>"
					"<p>Out-of-control values (recent): {values}</p>"
				).format(
					chart=self.chart_name,
					process=self.process_name,
					measurement=self.measurement_type,
					ucl=self.upper_control_limit,
					cl=self.center_line,
					lcl=self.lower_control_limit,
					values=ooc_summary,
				),
			}
		)
		cat.insert(ignore_permissions=True)
		frappe.msgprint(
			_("Corrective Action {0} created for out-of-control chart.").format(cat.name),
			alert=True,
		)


@frappe.whitelist()
def add_spc_data_point(chart_name, value):
	"""Whitelist wrapper for adding a data point from the client."""
	doc = frappe.get_doc("SPC Control Chart", chart_name)
	doc.check_permission("write")
	doc.add_data_point(flt(value))
	return {"status": doc.status, "data_points_count": len(doc.data_points)}
