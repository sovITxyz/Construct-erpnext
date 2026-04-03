# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


# El Salvador Labor Code overtime multipliers
SV_OVERTIME_RATES = {
    "Diurna": 2.0,      # Daytime overtime: 100% surcharge (base x 2)
    "Nocturna": 2.25,    # Nighttime overtime: 125% surcharge (base x 2.25)
    "Standard": 1.5,     # Generic/non-SV fallback
    "Double": 2.0,       # Generic double time
    "Custom": None,      # Use manually entered rate_multiplier
}


class OvertimeAdministration(Document):
    def validate(self):
        self._set_sv_rate_multiplier()
        self.compute_total()

    def _set_sv_rate_multiplier(self):
        """Auto-set rate_multiplier based on overtime_type for El Salvador."""
        if self.overtime_type in SV_OVERTIME_RATES:
            rate = SV_OVERTIME_RATES[self.overtime_type]
            if rate is not None:
                self.rate_multiplier = rate

    def compute_total(self):
        """Calculate total overtime amount: hours x base_rate x rate_multiplier."""
        self.total_amount = flt(
            flt(self.hours) * flt(self.base_rate) * flt(self.rate_multiplier), 2
        )
