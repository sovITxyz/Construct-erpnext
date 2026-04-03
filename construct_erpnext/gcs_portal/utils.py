import frappe

def get_client_projects(user=None):
    """Get projects accessible to a portal user."""
    if not user:
        user = frappe.session.user

    access = frappe.get_all(
        "Client Portal Access",
        filters={"user": user, "active": 1},
        fields=["name"],
    )
    if not access:
        return []

    projects = frappe.get_all(
        "Client Portal Project",
        filters={"parent": access[0].name},
        pluck="project",
    )
    return projects
