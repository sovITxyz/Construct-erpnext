# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def setup_el_salvador_payroll(company):
    """Create El Salvador payroll salary components and defaults."""

    components = [
        # (name, type, description, formula_or_amount, is_tax_applicable)
        ("ISSS Laboral", "Deduction", _("ISSS Employee Contribution 3%"), None, 0),
        ("ISSS Patronal", "Earning", _("ISSS Employer Contribution 7.5%"), None, 0),
        ("AFP Laboral", "Deduction", _("AFP Employee Contribution 7.25%"), None, 0),
        ("AFP Patronal", "Earning", _("AFP Employer Contribution 8.75%"), None, 0),
        ("Aguinaldo", "Earning", _("Christmas Bonus - Aguinaldo"), None, 0),
        ("ISR Renta", "Deduction", _("Income Tax Withholding"), None, 0),
    ]

    for comp_name, comp_type, description, formula, is_tax in components:
        if not frappe.db.exists("Salary Component", comp_name):
            sc = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": comp_name,
                "salary_component_abbr": comp_name.replace(" ", "_")[:10].upper(),
                "type": comp_type,
                "description": description,
                "is_tax_applicable": is_tax,
                "company": company,
            })
            sc.insert(ignore_permissions=True, ignore_if_duplicate=True)

    frappe.msgprint(_("El Salvador payroll components created for {0}").format(company))


def calculate_isss(gross_salary, isss_ceiling=1000.0):
    """Calculate ISSS contributions.

    Employee: 3% of gross salary (capped at ceiling)
    Employer: 7.5% of gross salary (capped at ceiling)
    """
    base = min(flt(gross_salary), flt(isss_ceiling))
    return {
        "employee": flt(base * 0.03, 2),
        "employer": flt(base * 0.075, 2),
    }


def calculate_afp(gross_salary):
    """Calculate AFP contributions.

    Employee: 7.25% of gross salary
    Employer: 8.75% of gross salary
    """
    return {
        "employee": flt(flt(gross_salary) * 0.0725, 2),
        "employer": flt(flt(gross_salary) * 0.0875, 2),
    }


def calculate_aguinaldo(employee):
    """Calculate Aguinaldo (13th month / Christmas bonus) for an employee.

    El Salvador Labor Code:
    - 1 to 3 years tenure: 10 days of salary
    - 3 to 10 years tenure: 15 days of salary
    - 10+ years tenure: 18 days of salary

    Paid between December 12-20 each year.
    """
    from frappe.utils import getdate, date_diff, nowdate

    emp = frappe.get_cached_doc("Employee", employee) if isinstance(employee, str) else employee

    if not emp.date_of_joining:
        return 0

    today = getdate(nowdate())
    tenure_days = date_diff(today, getdate(emp.date_of_joining))
    tenure_years = flt(tenure_days / 365.25, 1)

    if tenure_years < 1:
        # Pro-rate for first year
        days_entitled = flt(10 * tenure_years / 1, 2)
    elif tenure_years < 3:
        days_entitled = 10
    elif tenure_years < 10:
        days_entitled = 15
    else:
        days_entitled = 18

    # Calculate daily salary from monthly base
    # Try to get from Salary Structure Assignment
    monthly_salary = flt(frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": emp.name, "docstatus": 1},
        "base",
        order_by="from_date desc",
    ))

    if not monthly_salary:
        monthly_salary = flt(emp.ctc) or 0  # fallback to CTC

    daily_salary = flt(monthly_salary / 30, 2)  # El Salvador uses 30-day month

    return flt(daily_salary * days_entitled, 2)


def calculate_isr_renta(taxable_income):
    """Calculate ISR (Impuesto sobre la Renta) monthly withholding.

    El Salvador progressive monthly tax table (approximate):
    - $0.01 to $472.00: No tax
    - $472.01 to $895.24: 10% on excess over $472.00, plus $17.67
    - $895.25 to $2,038.10: 20% on excess over $895.24, plus $60.00
    - Over $2,038.10: 30% on excess over $2,038.10, plus $288.57
    """
    income = flt(taxable_income)

    if income <= 472.00:
        return 0
    elif income <= 895.24:
        return flt((income - 472.00) * 0.10 + 17.67, 2)
    elif income <= 2038.10:
        return flt((income - 895.24) * 0.20 + 60.00, 2)
    else:
        return flt((income - 2038.10) * 0.30 + 288.57, 2)
