import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in.", frappe.PermissionError)

    project_name = frappe.form_dict.get("project")
    if not project_name:
        frappe.throw("Project not specified.", frappe.ValidationError)

    # verify access
    access = frappe.get_all(
        "Client Portal Access",
        filters={"user": user, "active": 1},
    )
    accessible_projects = []
    for a in access:
        linked = frappe.get_all(
            "Client Portal Project",
            filters={"parent": a.name},
            pluck="project",
        )
        accessible_projects.extend(linked)

    if project_name not in accessible_projects:
        frappe.throw("You do not have access to this project.", frappe.PermissionError)

    project = frappe.get_doc("Project", project_name)
    tasks = frappe.get_all(
        "Task",
        filters={"project": project_name},
        fields=["subject", "status", "progress", "exp_end_date"],
        order_by="exp_end_date asc",
        limit_page_length=50,
    )
    advancements = frappe.get_all(
        "Physical Advancement",
        filters={"project": project_name, "docstatus": 1},
        fields=["period_date", "advancement_type", "advancement_pct"],
        order_by="period_date desc",
        limit_page_length=20,
    )

    context.project = project
    context.tasks = tasks
    context.advancements = advancements
    context.title = project.project_name
