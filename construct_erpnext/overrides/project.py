import frappe
from erpnext.projects.doctype.project.project import Project


class ConstructProject(Project):
    def validate(self):
        super().validate()
        self.update_budget_summary()
        self.update_advancement_summary()

    def update_budget_summary(self):
        """Pull total estimated and real costs from linked Construction Budget."""
        budgets = frappe.get_all(
            "Construction Budget",
            filters={"project": self.name, "docstatus": 1},
            fields=["total_estimated_amount", "total_real_cost"],
        )
        if budgets:
            total_estimated = sum(b.total_estimated_amount or 0 for b in budgets)
            total_real = sum(b.total_real_cost or 0 for b in budgets)
            self.estimated_costing = total_estimated
            self.total_costing_amount = total_real

    def update_advancement_summary(self):
        """Update project percent_complete from latest Physical Advancement."""
        latest = frappe.db.get_value(
            "Physical Advancement",
            filters={"project": self.name, "advancement_type": "Real", "docstatus": 1},
            fieldname="advancement_pct",
            order_by="period_date desc",
        )
        if latest is not None:
            self.percent_complete = latest

    def get_dashboard_data(self):
        """Override dashboard to add links to construction-specific DocTypes."""
        data = super().get_dashboard_data() if hasattr(super(), "get_dashboard_data") else {
            "fieldname": "project",
            "non_standard_fieldnames": {},
            "transactions": [],
        }

        construction_links = [
            {
                "label": "Construction Budget",
                "items": ["Construction Budget"],
            },
            {
                "label": "Advancement & Scheduling",
                "items": ["Physical Advancement", "Activity Schedule"],
            },
            {
                "label": "Subcontracts & Resources",
                "items": ["Subcontract", "Equipment Usage Log", "Labor Hour Entry"],
            },
            {
                "label": "Cost Tracking",
                "items": ["Project Cost Entry"],
            },
        ]

        if "transactions" not in data:
            data["transactions"] = []

        data["transactions"].extend(construction_links)

        return data
