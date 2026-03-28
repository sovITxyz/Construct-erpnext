import frappe

def get_context(context):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Please log in.", frappe.PermissionError)

    customer = frappe.db.get_value("Customer", {"portal_users": [["user", "=", user]]}, "name")
    if not customer:
        contact_names = frappe.get_all("Contact", filters={"user": user}, pluck="name")
        if contact_names:
            customer = frappe.db.get_value(
                "Dynamic Link",
                {"link_doctype": "Customer", "parenttype": "Contact", "parent": ["in", contact_names]},
                "link_name",
            )

    payments = []
    if customer:
        payments = frappe.get_all(
            "Payment Entry",
            filters={"party_type": "Customer", "party": customer, "docstatus": 1},
            fields=["name", "posting_date", "paid_amount", "mode_of_payment", "reference_no"],
            order_by="posting_date desc",
            limit_page_length=100,
        )

    context.payments = payments
    context.title = "Payment History"
