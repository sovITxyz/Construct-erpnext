import frappe

@frappe.whitelist()
def authorize_advancement(advancement, authorized_pct, comments=None):
    """Portal API to authorize a physical advancement."""
    user = frappe.session.user

    from construct_erpnext.gcs_portal.utils import get_client_projects
    accessible = get_client_projects(user)

    adv = frappe.get_doc("Physical Advancement", advancement)
    if adv.project not in accessible:
        frappe.throw("Access denied.", frappe.PermissionError)

    can_auth = frappe.db.get_value(
        "Client Portal Access",
        {"user": user, "active": 1},
        "can_authorize_advancement",
    )
    if not can_auth:
        frappe.throw("You are not authorized to approve advancements.", frappe.PermissionError)

    # Create a client-authorized advancement entry
    new_adv = frappe.new_doc("Physical Advancement")
    new_adv.project = adv.project
    new_adv.task = adv.task
    new_adv.advancement_pct = float(authorized_pct)
    new_adv.period_type = adv.period_type
    new_adv.period_date = adv.period_date
    new_adv.advancement_type = "Client Authorized"
    new_adv.remarks = comments or ""
    new_adv.insert(ignore_permissions=True)
    new_adv.submit()

    frappe.msgprint(f"Advancement authorized at {authorized_pct}%.")
    frappe.response["type"] = "redirect"
    frappe.response["location"] = "/advancement-auth"
