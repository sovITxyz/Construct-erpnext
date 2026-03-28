frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Collection Document"), function () {
                frappe.new_doc("Collection Document", {
                    customer: frm.doc.customer,
                    sales_invoice: frm.doc.name,
                    amount: frm.doc.outstanding_amount,
                    company: frm.doc.company,
                });
            }, __("Create"));
        }
    },
});
