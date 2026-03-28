import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in to view your projects.", frappe.PermissionError)

    project_names = []
    access_records = frappe.get_all(
        "Client Portal Access",
        filters={"user": user, "active": 1},
    )
    for access in access_records:
        linked = frappe.get_all(
            "Client Portal Project",
            filters={"parent": access.name},
            pluck="project",
        )
        project_names.extend(linked)

    projects = []
    for pname in project_names:
        try:
            proj = frappe.get_doc("Project", pname)
            projects.append(proj)
        except frappe.DoesNotExistError:
            continue

    context.projects = projects
    context.title = "My Projects"
