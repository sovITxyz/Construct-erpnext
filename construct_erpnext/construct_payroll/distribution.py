# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe


def distribute_costs(doc, method):
	"""Distribute salary slip costs to projects, equipment, and departments.

	Called via doc_events hook on Salary Slip on_submit.
	"""
	pass
