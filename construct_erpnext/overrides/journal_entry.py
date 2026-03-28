import frappe
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry

class ConstructJournalEntry(JournalEntry):
    def validate(self):
        super().validate()
