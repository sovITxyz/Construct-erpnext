import frappe

def project_query_conditions(user):
    """Filter projects based on user's access scope."""
    if frappe.session.user == "Administrator":
        return ""

    scopes = frappe.get_all(
        "Access Scope",
        filters={"user": user, "scope_type": "Project"},
        pluck="scope_name",
    )
    if not scopes:
        return ""

    project_list = ", ".join(f"'{frappe.db.escape(s)}'" for s in scopes)
    return f"`tabProject`.name in ({project_list})"

def task_query_conditions(user):
    """Filter tasks based on user's project access scope."""
    if frappe.session.user == "Administrator":
        return ""

    scopes = frappe.get_all(
        "Access Scope",
        filters={"user": user, "scope_type": "Project"},
        pluck="scope_name",
    )
    if not scopes:
        return ""

    project_list = ", ".join(f"'{frappe.db.escape(s)}'" for s in scopes)
    return f"`tabTask`.project in ({project_list})"

def budget_query_conditions(user):
    """Filter construction budgets based on user's project access scope."""
    if frappe.session.user == "Administrator":
        return ""

    scopes = frappe.get_all(
        "Access Scope",
        filters={"user": user, "scope_type": "Project"},
        pluck="scope_name",
    )
    if not scopes:
        return ""

    project_list = ", ".join(f"'{frappe.db.escape(s)}'" for s in scopes)
    return f"`tabConstruction Budget`.project in ({project_list})"

def has_project_permission(doc, ptype, user):
    """Check if user has permission for a specific project."""
    if user == "Administrator":
        return True

    scopes = frappe.get_all(
        "Access Scope",
        filters={"user": user, "scope_type": "Project", "scope_name": doc.name},
        fields=["permission_level"],
    )
    if not scopes:
        return True  # no scope restriction configured

    level = scopes[0].permission_level
    if ptype == "read":
        return level in ("Read", "Write", "Full")
    if ptype in ("write", "create"):
        return level in ("Write", "Full")
    if ptype in ("delete", "submit", "cancel"):
        return level == "Full"

    return True

def has_budget_permission(doc, ptype, user):
    """Check budget permission via project scope."""
    if user == "Administrator":
        return True

    return has_project_permission(
        frappe._dict({"name": doc.project}), ptype, user
    )
