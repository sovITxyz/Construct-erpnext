frappe.ui.form.on("Payment Entry", {
    refresh(frm) {
        // Show check request link if applicable
        if (frm.doc.custom_check_request) {
            frm.add_custom_button(__("View Check Request"), function () {
                frappe.set_route("Form", "Check Request", frm.doc.custom_check_request);
            });
        }
    },
});
