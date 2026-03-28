import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in.", frappe.PermissionError)

    from construct_erpnext.construct_portal.utils import get_client_projects
    project_names = get_client_projects(user)

    projects = []
    for pname in project_names:
        try:
            proj = frappe.get_doc("Project", pname)
            files = frappe.get_all(
                "File",
                filters={"attached_to_doctype": "Project", "attached_to_name": pname, "is_private": 0},
                fields=["file_name", "file_url"],
            )
            proj.files = files
            projects.append(proj)
        except frappe.DoesNotExistError:
            continue

    context.projects = projects
    context.title = "Documents"
