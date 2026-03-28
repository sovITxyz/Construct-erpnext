# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe


def schedule_payment_reminders(doc, method):
	"""Schedule payment reminders when a Sales Invoice is submitted.

	Called via doc_events hook on Sales Invoice on_submit.
	"""
	pass


def send_payment_reminders():
	"""Send scheduled payment reminders for overdue invoices.

	Called daily via scheduler_events.
	"""
	pass
