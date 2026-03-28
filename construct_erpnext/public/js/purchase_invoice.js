frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Request Authorization"), function () {
                frappe.new_doc("Invoice Authorization", {
                    purchase_invoice: frm.doc.name,
                    company: frm.doc.company,
                });
            }, __("Create"));

            frm.add_custom_button(__("Request Check"), function () {
                frappe.new_doc("Check Request", {
                    supplier: frm.doc.supplier,
                    purchase_invoice: frm.doc.name,
                    amount: frm.doc.grand_total,
                    company: frm.doc.company,
                });
            }, __("Create"));
        }
    },
});
