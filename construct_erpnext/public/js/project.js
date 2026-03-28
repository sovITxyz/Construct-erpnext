frappe.ui.form.on("Project", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Construction Budget"), function () {
                frappe.set_route("List", "Construction Budget", {project: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Physical Advancement"), function () {
                frappe.set_route("List", "Physical Advancement", {project: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Cost Entries"), function () {
                frappe.set_route("List", "Project Cost Entry", {project: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Subcontracts"), function () {
                frappe.set_route("List", "Subcontract", {project: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Activity Schedule"), function () {
                frappe.set_route("List", "Activity Schedule", {project: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("New Budget"), function () {
                frappe.new_doc("Construction Budget", {project: frm.doc.name});
            }, __("Create"));

            frm.add_custom_button(__("Record Advancement"), function () {
                frappe.new_doc("Physical Advancement", {project: frm.doc.name});
            }, __("Create"));
        }
    },
});
