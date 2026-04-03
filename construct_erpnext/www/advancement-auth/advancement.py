import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in.", frappe.PermissionError)

    adv_name = frappe.form_dict.get("advancement")
    if not adv_name:
        frappe.throw("Advancement not specified.", frappe.ValidationError)

    advancement = frappe.get_doc("Physical Advancement", adv_name)

    from construct_erpnext.gcs_portal.utils import get_client_projects
    accessible = get_client_projects(user)
    if advancement.project not in accessible:
        frappe.throw("Access denied.", frappe.PermissionError)

    can_authorize = frappe.db.get_value(
        "Client Portal Access",
        {"user": user, "active": 1},
        "can_authorize_advancement",
    )

    context.advancement = advancement
    context.can_authorize = can_authorize
    context.title = f"Review {adv_name}"
