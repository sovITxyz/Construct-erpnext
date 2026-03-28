import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in.", frappe.PermissionError)

    customer = frappe.db.get_value("Customer", {"portal_users": [["user", "=", user]]}, "name")
    if not customer:
        customer_link = frappe.db.get_value(
            "Dynamic Link",
            {"link_doctype": "Customer", "parenttype": "Contact", "parent": ["in",
                frappe.get_all("Contact", filters={"user": user}, pluck="name")
            ]},
            "link_name",
        )
        customer = customer_link

    invoices = []
    if customer:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={"customer": customer, "docstatus": 1},
            fields=["name", "posting_date", "grand_total", "outstanding_amount"],
            order_by="posting_date desc",
            limit_page_length=100,
        )

    context.invoices = invoices
    context.title = "My Invoices"
