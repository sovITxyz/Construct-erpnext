# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe


def handle_check_status_change(doc, method):
	"""Handle status transitions for Check Request documents.

	Called via doc_events hook on Check Request on_update_after_submit.
	"""
	pass
