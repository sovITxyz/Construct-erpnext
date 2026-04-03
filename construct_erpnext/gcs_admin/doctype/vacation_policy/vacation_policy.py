# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, date_diff, nowdate


class VacationPolicy(Document):
    def validate(self):
        if self.country == "El Salvador":
            self._set_el_salvador_defaults()

    def _set_el_salvador_defaults(self):
        """Apply El Salvador vacation rules if no manual rules exist.

        El Salvador Labor Code:
        - 15 calendar days paid vacation after 1 year of continuous service
        - Vacation pay: regular daily salary + 30% bonus
        - No carryover required by law
        """
        if not self.rules or len(self.rules) == 0:
            self.append("rules", {
                "years_of_service_start": 1,
                "years_of_service_end": 99,
                "vacation_days_entitled": 15,
                "bonus_percentage": 30,
            })
            frappe.msgprint(
                _("El Salvador vacation rules applied: 15 days after 1 year with 30% bonus."),
                indicator="blue",
            )

    @staticmethod
    def get_sv_vacation_entitlement(employee):
        """Calculate vacation entitlement for an El Salvador employee.

        Returns dict with days_entitled and vacation_bonus_pct.
        """
        emp = frappe.get_cached_doc("Employee", employee) if isinstance(employee, str) else employee

        if not emp.date_of_joining:
            return {"days_entitled": 0, "vacation_bonus_pct": 0}

        today = getdate(nowdate())
        tenure_days = date_diff(today, getdate(emp.date_of_joining))
        tenure_years = flt(tenure_days / 365.25, 1)

        if tenure_years < 1:
            return {"days_entitled": 0, "vacation_bonus_pct": 0}

        return {
            "days_entitled": 15,
            "vacation_bonus_pct": 30,
            "tenure_years": tenure_years,
        }
