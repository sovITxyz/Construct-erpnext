import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in.", frappe.PermissionError)

    from construct_erpnext.construct_portal.utils import get_client_projects
    project_names = get_client_projects(user)

    advancements = []
    if project_names:
        advancements = frappe.get_all(
            "Physical Advancement",
            filters={
                "project": ["in", project_names],
                "advancement_type": "Real",
                "docstatus": 1,
            },
            fields=["name", "project", "period_date", "advancement_pct", "advancement_type"],
            order_by="period_date desc",
            limit_page_length=50,
        )

    context.advancements = advancements
    context.title = "Authorize Advancement"
