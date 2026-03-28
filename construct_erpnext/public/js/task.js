frappe.ui.form.on("Task", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.project) {
            frm.add_custom_button(__("Labor Hours"), function () {
                frappe.set_route("List", "Labor Hour Entry", {
                    project: frm.doc.project,
                    task: frm.doc.name,
                });
            }, __("View"));

            frm.add_custom_button(__("Equipment Usage"), function () {
                frappe.set_route("List", "Equipment Usage Log", {
                    project: frm.doc.project,
                    task: frm.doc.name,
                });
            }, __("View"));
        }
    },
});
