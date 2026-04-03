import frappe
from frappe.utils import now_datetime, get_datetime

def log_insert(doc, method):
    """Log document insertion to audit trail."""
    if not _is_tracked(doc.doctype):
        return
    if doc.doctype == "Audit Trail Entry":
        return  # prevent infinite recursion

    frappe.enqueue(
        _create_audit_entry,
        queue="short",
        doctype_name=doc.doctype,
        docname=doc.name,
        operation="Insert",
        user=frappe.session.user,
    )

def log_update(doc, method):
    """Log document updates to audit trail with field-level diffs."""
    if not _is_tracked(doc.doctype):
        return
    if doc.doctype in ("Audit Trail Entry", "Audit Trail Config"):
        return

    previous = doc.get_doc_before_save()
    if not previous:
        return

    changed_fields = _get_changed_fields(doc, previous)
    if not changed_fields:
        return

    for field_name, old_val, new_val in changed_fields:
        frappe.enqueue(
            _create_audit_entry,
            queue="short",
            doctype_name=doc.doctype,
            docname=doc.name,
            operation="Update",
            user=frappe.session.user,
            field_name=field_name,
            old_value=str(old_val) if old_val is not None else "",
            new_value=str(new_val) if new_val is not None else "",
        )

def log_delete(doc, method):
    """Log document deletion to audit trail."""
    if not _is_tracked(doc.doctype):
        return
    if doc.doctype == "Audit Trail Entry":
        return

    frappe.enqueue(
        _create_audit_entry,
        queue="short",
        doctype_name=doc.doctype,
        docname=doc.name,
        operation="Delete",
        user=frappe.session.user,
    )

def process_audit_queue():
    """Scheduled job to process any queued audit entries."""
    pass  # placeholder for batch processing if needed

def _is_tracked(doctype):
    """Check if a doctype is configured for audit tracking."""
    config = frappe.db.get_value(
        "Audit Trail Config",
        {"tracked_doctype": doctype, "active": 1},
        "name",
        cache=True,
    )
    return bool(config)

def _get_changed_fields(doc, previous):
    """Return list of (field_name, old_value, new_value) tuples for changed fields."""
    changed = []
    config = frappe.db.get_value(
        "Audit Trail Config",
        {"tracked_doctype": doc.doctype, "active": 1},
        ["track_all_fields", "name"],
        as_dict=True,
    )
    if not config:
        return changed

    if config.track_all_fields:
        fields_to_check = [df.fieldname for df in doc.meta.fields if df.fieldtype not in ("Section Break", "Column Break", "Tab Break")]
    else:
        tracked = frappe.get_all(
            "Audit Trail Field",
            filters={"parent": config.name},
            pluck="field_name",
        )
        fields_to_check = tracked

    for field in fields_to_check:
        old_val = previous.get(field)
        new_val = doc.get(field)
        if old_val != new_val:
            changed.append((field, old_val, new_val))

    return changed

def _create_audit_entry(doctype_name, docname, operation, user, field_name=None, old_value=None, new_value=None):
    """Create an Audit Trail Entry record."""
    entry = frappe.new_doc("Audit Trail Entry")
    entry.tracked_doctype = doctype_name
    entry.tracked_name = docname
    entry.operation = operation
    entry.field_name = field_name or ""
    entry.old_value = old_value or ""
    entry.new_value = new_value or ""
    entry.changed_by = user
    entry.change_timestamp = now_datetime()
    entry.ip_address = frappe.local.request_ip if hasattr(frappe.local, "request_ip") else ""
    entry.session_id = frappe.session.sid or ""
    entry.flags.ignore_permissions = True
    entry.insert()
