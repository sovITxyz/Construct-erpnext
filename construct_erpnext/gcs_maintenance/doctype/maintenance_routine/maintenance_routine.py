# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today

# Frequency to number of days mapping
FREQUENCY_DAYS = {
	"Daily": 1,
	"Weekly": 7,
	"Monthly": 30,
	"Quarterly": 90,
	"Semi-Annual": 182,
	"Annual": 365,
}


class MaintenanceRoutine(Document):
	def validate(self):
		self._calculate_next_due()

	@frappe.whitelist()
	def mark_performed(self):
		"""Mark this routine as performed today and recalculate next_due."""
		self.last_performed = today()
		self._calculate_next_due()
		self.save(ignore_permissions=True)
		frappe.msgprint(
			_("Routine marked as performed. Next due: {0}").format(self.next_due),
			alert=True,
		)

	def _calculate_next_due(self):
		days = FREQUENCY_DAYS.get(self.frequency)
		if not days:
			return

		base_date = getdate(self.last_performed) if self.last_performed else getdate(today())
		self.next_due = add_days(base_date, days)


@frappe.whitelist()
def mark_routine_performed(routine_name):
	"""Whitelist wrapper for client-side calls."""
	doc = frappe.get_doc("Maintenance Routine", routine_name)
	doc.check_permission("write")
	doc.mark_performed()
	return {"last_performed": str(doc.last_performed), "next_due": str(doc.next_due)}
