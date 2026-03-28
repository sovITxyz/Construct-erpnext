import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class AuditTrailExport(Document):
    def validate(self):
        if self.date_range_start and self.date_range_end:
            if self.date_range_start > self.date_range_end:
                frappe.throw(_("Date Range Start must be before Date Range End."))

    def before_save(self):
        if not self.exported_by:
            self.exported_by = frappe.session.user
        if not self.export_date:
            self.export_date = now_datetime()
