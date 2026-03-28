import frappe
from frappe.model.document import Document


class MetaAuditEntry(Document):
    def on_trash(self):
        frappe.throw("Meta Audit Entries cannot be deleted.")
