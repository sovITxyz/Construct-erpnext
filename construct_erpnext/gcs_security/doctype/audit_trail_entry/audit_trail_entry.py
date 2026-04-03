import frappe
from frappe.model.document import Document


class AuditTrailEntry(Document):
    def before_save(self):
        # Append-only: prevent updates to existing records
        if not self.is_new():
            frappe.throw("Audit Trail Entries cannot be modified after creation.")

    def on_trash(self):
        frappe.throw("Audit Trail Entries cannot be deleted.")
