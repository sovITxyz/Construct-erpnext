import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class AuditTrailConfig(Document):
    def validate(self):
        if self.active and not self.activated_by:
            self.activated_by = frappe.session.user
            self.activated_date = nowdate()

    def on_update(self):
        # Clear cache so audit hooks pick up changes immediately
        frappe.cache.delete_value(f"audit_config_{self.tracked_doctype}")
