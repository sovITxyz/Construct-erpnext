import frappe
from frappe import _
from frappe.utils import flt
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

# Movement types that map to earnings on the salary slip
_EARNING_MOVEMENTS = {"Bonus", "Overtime", "Task Compensation", "Benefit"}
# Movement types that map to deductions on the salary slip
_DEDUCTION_MOVEMENTS = {"Loan Deduction", "Social Security", "Tax Withholding"}

# Default salary component per movement type (must exist in the site)
_COMPONENT_MAP = {
    "Bonus": "Bonus",
    "Overtime": "Overtime",
    "Task Compensation": "Task Compensation",
    "Benefit": "Benefit",
    "Loan Deduction": "Loan Deduction",
    "Social Security": "Social Security",
    "Tax Withholding": "Tax Withholding",
}


class ConstructSalarySlip(SalarySlip):
    def validate(self):
        super().validate()
        self._apply_payroll_movements()

    def _apply_payroll_movements(self):
        """Inject active Payroll Movements as additional earnings or deductions."""
        if not self.employee:
            return

        movements = frappe.get_all(
            "Payroll Movement",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "status": ["in", ["Applied", "Authorized"]],
                "movement_type": ["in", list(_EARNING_MOVEMENTS | _DEDUCTION_MOVEMENTS)],
            },
            fields=["name", "movement_type", "amount", "recurrence", "remaining_balance"],
        )

        for mv in movements:
            # Skip non-recurring movements that have already been processed
            if mv.recurrence == "One-time":
                continue

            # For "Until Paid" recurrence, skip if nothing remains
            if mv.recurrence == "Until Paid" and flt(mv.remaining_balance) <= 0:
                continue

            component = _COMPONENT_MAP.get(mv.movement_type)
            if not component:
                continue

            amount = flt(mv.amount)
            # For "Until Paid", cap at remaining balance
            if mv.recurrence == "Until Paid":
                amount = min(amount, flt(mv.remaining_balance))

            if mv.movement_type in _EARNING_MOVEMENTS:
                self._add_movement_to_earnings(component, amount, mv.name)
            elif mv.movement_type in _DEDUCTION_MOVEMENTS:
                self._add_movement_to_deductions(component, amount, mv.name)

    def _add_movement_to_earnings(self, component, amount, movement_name):
        """Add an earning row if the component is not already present from this movement."""
        # Avoid duplicates from the same movement
        for row in self.earnings:
            if (
                row.salary_component == component
                and flt(row.amount) == flt(amount)
            ):
                return

        self.append(
            "earnings",
            {
                "salary_component": component,
                "amount": amount,
                "default_amount": 0,
                "additional_amount": amount,
            },
        )

    def _add_movement_to_deductions(self, component, amount, movement_name):
        """Add a deduction row if the component is not already present from this movement."""
        for row in self.deductions:
            if (
                row.salary_component == component
                and flt(row.amount) == flt(amount)
            ):
                return

        self.append(
            "deductions",
            {
                "salary_component": component,
                "amount": amount,
                "default_amount": 0,
                "additional_amount": amount,
            },
        )
