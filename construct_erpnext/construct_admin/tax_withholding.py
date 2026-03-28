# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe


def calculate_withholdings(doc, method):
	"""Calculate tax withholdings on a Purchase Invoice during validation.

	Called via doc_events hook on Purchase Invoice validate.
	"""
	pass
