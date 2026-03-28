import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

class ConstructSalarySlip(SalarySlip):
    def validate(self):
        super().validate()
