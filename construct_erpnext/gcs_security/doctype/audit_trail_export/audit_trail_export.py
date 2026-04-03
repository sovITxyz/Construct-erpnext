import csv
import io
import json as json_lib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime_str

ENTRY_FIELDS = [
    "name",
    "tracked_doctype",
    "tracked_name",
    "operation",
    "field_name",
    "old_value",
    "new_value",
    "changed_by",
    "change_timestamp",
    "ip_address",
    "session_id",
]


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

    @frappe.whitelist()
    def generate_export(self):
        """Query Audit Trail Entries matching filters and generate a file export."""
        entries = self._query_entries()

        if self.export_format == "JSON":
            content, extension = self._generate_json(entries), "json"
        else:
            content, extension = self._generate_csv(entries), "csv"

        timestamp = now_datetime().strftime("%Y%m%d_%H%M%S")
        file_name = f"audit_export_{timestamp}.{extension}"

        file_doc = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "content": content,
                "is_private": 1,
                "attached_to_doctype": "Audit Trail Export",
                "attached_to_name": self.name,
            }
        )
        file_doc.insert(ignore_permissions=True)

        self.exported_file = file_doc.file_url
        self.record_count = len(entries)
        self.exported_by = frappe.session.user
        self.export_date = now_datetime()
        self.save(ignore_permissions=True)

        self._log_meta_audit(len(entries))
        frappe.msgprint(
            _("Exported {0} records.").format(len(entries)), alert=True
        )

    # --- internal helpers ---

    def _query_entries(self):
        filters = {}

        if self.date_range_start:
            filters["change_timestamp"] = [">=", get_datetime_str(self.date_range_start)]
        if self.date_range_end:
            # Combine with existing filter when both dates are set
            if "change_timestamp" in filters:
                filters["change_timestamp"] = [
                    "between",
                    [
                        get_datetime_str(self.date_range_start),
                        get_datetime_str(self.date_range_end) + " 23:59:59",
                    ],
                ]
            else:
                filters["change_timestamp"] = [
                    "<=",
                    get_datetime_str(self.date_range_end) + " 23:59:59",
                ]

        if self.doctype_filter:
            filters["tracked_doctype"] = self.doctype_filter
        if self.user_filter:
            filters["changed_by"] = self.user_filter

        return frappe.get_all(
            "Audit Trail Entry",
            filters=filters,
            fields=ENTRY_FIELDS,
            order_by="change_timestamp asc",
            limit_page_length=0,
        )

    def _generate_csv(self, entries):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=ENTRY_FIELDS)
        writer.writeheader()
        for entry in entries:
            # Ensure datetimes are serialized as strings
            row = {k: str(v) if v is not None else "" for k, v in entry.items()}
            writer.writerow(row)
        return output.getvalue()

    def _generate_json(self, entries):
        serializable = []
        for entry in entries:
            row = {k: str(v) if v is not None else None for k, v in entry.items()}
            serializable.append(row)
        return json_lib.dumps(serializable, indent=2, ensure_ascii=False)

    def _log_meta_audit(self, record_count):
        frappe.get_doc(
            {
                "doctype": "Meta Audit Entry",
                "action": "Export",
                "audit_entry_reference": self.name,
                "details": (
                    f"Exported {record_count} audit trail entries. "
                    f"Filters: doctype={self.doctype_filter or 'All'}, "
                    f"user={self.user_filter or 'All'}, "
                    f"date_range={self.date_range_start} to {self.date_range_end}. "
                    f"Format: {self.export_format}."
                ),
                "performed_by": frappe.session.user,
                "action_timestamp": now_datetime(),
            }
        ).insert(ignore_permissions=True)


@frappe.whitelist()
def generate_audit_export(export_name):
    """Whitelist wrapper to trigger audit export generation from the client."""
    doc = frappe.get_doc("Audit Trail Export", export_name)
    doc.check_permission("write")
    doc.generate_export()
    return {"record_count": doc.record_count, "exported_file": doc.exported_file}
