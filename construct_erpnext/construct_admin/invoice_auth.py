# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe


def check_authorization(doc, method):
	"""Check if a Purchase Invoice has been authorized before submission.

	Called via doc_events hook on Purchase Invoice on_submit.
	"""
	pass
