frappe.ui.form.on("Asset", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Components"), function () {
                frappe.set_route("List", "Asset Component", {parent_asset: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Failure Analysis"), function () {
                frappe.set_route("List", "Failure Analysis", {asset: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Downtime Records"), function () {
                frappe.set_route("List", "Downtime Record", {asset: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Maintenance Routines"), function () {
                frappe.set_route("List", "Maintenance Routine", {asset: frm.doc.name});
            }, __("View"));
        }
    },
});
