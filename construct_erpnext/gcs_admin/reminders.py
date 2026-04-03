# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, date_diff, flt, add_days


def schedule_payment_reminders(doc, method):
	"""Schedule payment reminders when a Sales Invoice is submitted.

	Called via doc_events hook on Sales Invoice on_submit.
	Looks up or creates a Payment Reminder Schedule for the customer.
	"""
	if not doc.customer:
		return

	# Check if a schedule already exists for this customer and company
	existing = frappe.db.exists(
		"Payment Reminder Schedule",
		{
			"customer": doc.customer,
			"company": doc.company,
			"active": 1,
		},
	)

	if existing:
		return

	# Create a default reminder schedule for the customer
	schedule = frappe.new_doc("Payment Reminder Schedule")
	schedule.schedule_name = _("Auto Reminder - {0}").format(doc.customer_name or doc.customer)
	schedule.customer = doc.customer
	schedule.active = 1
	schedule.days_before_due = 3
	schedule.days_after_due_1 = 1
	schedule.days_after_due_2 = 7
	schedule.days_after_due_3 = 14
	schedule.company = doc.company
	schedule.insert(ignore_permissions=True)


def send_payment_reminders():
	"""Send scheduled payment reminders for overdue invoices.

	Called daily via scheduler_events.
	Queries all Sales Invoices that are overdue and matches them against
	active Payment Reminder Schedules to send email notifications.
	"""
	today = getdate(nowdate())

	# Get all active reminder schedules
	schedules = frappe.get_all(
		"Payment Reminder Schedule",
		filters={"active": 1},
		fields=[
			"name", "customer", "company",
			"days_before_due", "days_after_due_1", "days_after_due_2", "days_after_due_3",
			"email_template_before", "email_template_after",
		],
	)

	if not schedules:
		return

	# Build a lookup by (customer, company)
	schedule_map = {}
	for s in schedules:
		key = (s.customer, s.company)
		schedule_map[key] = s

	# Get all unpaid Sales Invoices with outstanding amounts
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"customer": ["in", [s.customer for s in schedules]],
		},
		fields=[
			"name", "customer", "customer_name", "company",
			"due_date", "outstanding_amount", "grand_total",
			"contact_email",
		],
	)

	for inv in invoices:
		key = (inv.customer, inv.company)
		schedule = schedule_map.get(key)
		if not schedule:
			continue

		due_date = getdate(inv.due_date)
		days_until_due = date_diff(due_date, today)  # positive = before due, negative = overdue

		should_send = False
		reminder_type = None

		# Before due date reminder
		if days_until_due > 0 and schedule.days_before_due:
			if days_until_due == int(schedule.days_before_due):
				should_send = True
				reminder_type = "before_due"

		# After due date reminders
		if days_until_due < 0:
			days_overdue = abs(days_until_due)

			if schedule.days_after_due_1 and days_overdue == int(schedule.days_after_due_1):
				should_send = True
				reminder_type = "after_due_1"
			elif schedule.days_after_due_2 and days_overdue == int(schedule.days_after_due_2):
				should_send = True
				reminder_type = "after_due_2"
			elif schedule.days_after_due_3 and days_overdue == int(schedule.days_after_due_3):
				should_send = True
				reminder_type = "after_due_3"

		if not should_send:
			continue

		_send_reminder_email(inv, schedule, reminder_type)


def _send_reminder_email(invoice, schedule, reminder_type):
	"""Send a payment reminder email for a specific invoice."""
	# Determine recipient
	recipient = invoice.contact_email
	if not recipient:
		# Try to get primary contact email for the customer
		recipient = frappe.db.get_value(
			"Contact",
			{"link_doctype": "Customer", "link_name": invoice.customer, "is_primary_contact": 1},
			"email_id",
		)
	if not recipient:
		# Try customer email
		recipient = frappe.db.get_value("Customer", invoice.customer, "email_id")

	if not recipient:
		frappe.log_error(
			title=_("Payment Reminder - No Email"),
			message=_("No email address found for customer {0} (Invoice {1})").format(
				invoice.customer, invoice.name
			),
		)
		return

	# Determine template
	template_name = None
	if reminder_type == "before_due" and schedule.email_template_before:
		template_name = schedule.email_template_before
	elif reminder_type and reminder_type.startswith("after_due") and schedule.email_template_after:
		template_name = schedule.email_template_after

	subject = _("Payment Reminder: Invoice {0}").format(invoice.name)
	message = None

	if template_name:
		try:
			template = frappe.get_doc("Email Template", template_name)
			context = {
				"invoice_name": invoice.name,
				"customer_name": invoice.customer_name or invoice.customer,
				"outstanding_amount": invoice.outstanding_amount,
				"grand_total": invoice.grand_total,
				"due_date": invoice.due_date,
			}
			subject = frappe.render_template(template.subject, context)
			message = frappe.render_template(template.response, context)
		except Exception:
			frappe.log_error(
				title=_("Payment Reminder Template Error"),
				message=frappe.get_traceback(),
			)

	if not message:
		# Default message
		due_date = getdate(invoice.due_date)
		today = getdate(nowdate())
		if due_date < today:
			message = _(
				"Dear {0},<br><br>"
				"This is a reminder that Invoice <b>{1}</b> with an outstanding amount of "
				"<b>{2}</b> was due on <b>{3}</b>.<br><br>"
				"Please arrange payment at your earliest convenience.<br><br>"
				"Thank you."
			).format(
				invoice.customer_name or invoice.customer,
				invoice.name,
				frappe.format_value(invoice.outstanding_amount, {"fieldtype": "Currency"}),
				frappe.format_value(invoice.due_date, {"fieldtype": "Date"}),
			)
		else:
			message = _(
				"Dear {0},<br><br>"
				"This is a friendly reminder that Invoice <b>{1}</b> with an amount of "
				"<b>{2}</b> is due on <b>{3}</b>.<br><br>"
				"Thank you."
			).format(
				invoice.customer_name or invoice.customer,
				invoice.name,
				frappe.format_value(invoice.outstanding_amount, {"fieldtype": "Currency"}),
				frappe.format_value(invoice.due_date, {"fieldtype": "Date"}),
			)

	frappe.sendmail(
		recipients=[recipient],
		subject=subject,
		message=message,
		reference_doctype="Sales Invoice",
		reference_name=invoice.name,
		now=True,
	)
