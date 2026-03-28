frappe.ui.form.on("Salary Slip", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Cost Distribution"), function () {
                frappe.set_route("List", "Payroll Cost Distribution", {salary_slip: frm.doc.name});
            }, __("View"));

            frm.add_custom_button(__("Distribute Costs"), function () {
                frappe.new_doc("Payroll Cost Distribution", {
                    salary_slip: frm.doc.name,
                    employee: frm.doc.employee,
                    total_amount: frm.doc.net_pay,
                    company: frm.doc.company,
                });
            }, __("Create"));
        }
    },
});
