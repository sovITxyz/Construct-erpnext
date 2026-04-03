# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

# Movement types that result in Additional Salary earnings
EARNING_TYPES = {"Bonus", "Overtime", "Task Compensation", "Benefit"}
# Movement types that result in Additional Salary deductions
DEDUCTION_TYPES = {"Social Security", "Tax Withholding"}

# Mapping from movement_type to a default salary component name.
# Sites should create matching Salary Component records.
SALARY_COMPONENT_MAP = {
	"Bonus": "Bonus",
	"Overtime": "Overtime",
	"Task Compensation": "Task Compensation",
	"Benefit": "Benefit",
	"Social Security": "Social Security",
	"Tax Withholding": "Tax Withholding",
}


class PayrollMovement(Document):
	def validate(self):
		self._validate_amount()
		self._validate_employee()

	def on_submit(self):
		if self.movement_type == "Loan Issuance":
			self._create_employee_loan()
		elif self.movement_type == "Loan Deduction":
			self._apply_loan_deduction()
		elif self.movement_type in EARNING_TYPES | DEDUCTION_TYPES:
			self._create_additional_salary()

	def on_cancel(self):
		if self.movement_type == "Loan Issuance":
			self._cancel_employee_loan()
		elif self.movement_type == "Loan Deduction":
			self._reverse_loan_deduction()
		elif self.movement_type in EARNING_TYPES | DEDUCTION_TYPES:
			self._cancel_additional_salary()

	# --- validation ---

	def _validate_amount(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero."))

	def _validate_employee(self):
		if not self.employee:
			frappe.throw(_("Employee is required."))

	# --- Loan Issuance ---

	def _create_employee_loan(self):
		loan = frappe.get_doc(
			{
				"doctype": "Employee Loan",
				"employee": self.employee,
				"loan_amount": flt(self.amount),
				"remaining_balance": flt(self.amount),
				"total_deducted": 0,
				"installment_amount": flt(self.amount),  # default single installment
				"deduction_start_date": self.effective_date,
				"status": "Active",
				"company": self.company,
			}
		)
		loan.insert(ignore_permissions=True)
		frappe.db.set_value(
			"Payroll Movement", self.name, "remaining_balance", flt(self.amount)
		)
		frappe.msgprint(
			_("Employee Loan {0} created.").format(loan.name), alert=True
		)

	def _cancel_employee_loan(self):
		loans = frappe.get_all(
			"Employee Loan",
			filters={
				"employee": self.employee,
				"loan_amount": flt(self.amount),
				"status": "Active",
			},
			order_by="creation desc",
			limit=1,
			pluck="name",
		)
		if loans:
			loan = frappe.get_doc("Employee Loan", loans[0])
			loan.status = "Cancelled"
			loan.save(ignore_permissions=True)

	# --- Loan Deduction ---

	def _apply_loan_deduction(self):
		loan = self._get_active_loan()
		if not loan:
			frappe.throw(
				_("No active Employee Loan found for {0}.").format(self.employee_name or self.employee)
			)

		deduction = flt(self.amount)
		loan.total_deducted = flt(loan.total_deducted) + deduction
		loan.remaining_balance = flt(loan.loan_amount) - flt(loan.total_deducted)

		if flt(loan.installment_amount):
			import math
			loan.installments_remaining = max(
				0,
				math.ceil(flt(loan.remaining_balance) / flt(loan.installment_amount)),
			)
		else:
			loan.installments_remaining = 0

		if flt(loan.remaining_balance) <= 0:
			loan.remaining_balance = 0
			loan.installments_remaining = 0
			loan.status = "Fully Paid"

		loan.save(ignore_permissions=True)
		frappe.db.set_value(
			"Payroll Movement", self.name, "remaining_balance", flt(loan.remaining_balance)
		)

	def _reverse_loan_deduction(self):
		loan = self._get_latest_loan()
		if not loan:
			return

		deduction = flt(self.amount)
		loan.total_deducted = max(0, flt(loan.total_deducted) - deduction)
		loan.remaining_balance = flt(loan.loan_amount) - flt(loan.total_deducted)

		if flt(loan.installment_amount):
			import math
			loan.installments_remaining = math.ceil(
				flt(loan.remaining_balance) / flt(loan.installment_amount)
			)
		else:
			loan.installments_remaining = 0

		if flt(loan.remaining_balance) > 0 and loan.status == "Fully Paid":
			loan.status = "Active"

		loan.save(ignore_permissions=True)

	def _get_active_loan(self):
		loans = frappe.get_all(
			"Employee Loan",
			filters={"employee": self.employee, "status": "Active"},
			order_by="creation asc",
			limit=1,
			pluck="name",
		)
		return frappe.get_doc("Employee Loan", loans[0]) if loans else None

	def _get_latest_loan(self):
		loans = frappe.get_all(
			"Employee Loan",
			filters={
				"employee": self.employee,
				"status": ["in", ["Active", "Fully Paid"]],
			},
			order_by="creation desc",
			limit=1,
			pluck="name",
		)
		return frappe.get_doc("Employee Loan", loans[0]) if loans else None

	# --- Additional Salary ---

	def _create_additional_salary(self):
		component = SALARY_COMPONENT_MAP.get(self.movement_type)
		if not component:
			frappe.throw(
				_("No salary component mapping for movement type {0}.").format(
					self.movement_type
				)
			)

		is_recurring = self.recurrence == "Monthly"

		add_sal = frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"employee": self.employee,
				"salary_component": component,
				"amount": flt(self.amount),
				"payroll_date": self.effective_date,
				"company": self.company,
				"recurring": 1 if is_recurring else 0,
				"ref_doctype": "Payroll Movement",
				"ref_docname": self.name,
			}
		)
		add_sal.insert(ignore_permissions=True)
		add_sal.submit()

	def _cancel_additional_salary(self):
		linked = frappe.get_all(
			"Additional Salary",
			filters={
				"ref_doctype": "Payroll Movement",
				"ref_docname": self.name,
				"docstatus": 1,
			},
			pluck="name",
		)
		for name in linked:
			add_sal = frappe.get_doc("Additional Salary", name)
			add_sal.cancel()
