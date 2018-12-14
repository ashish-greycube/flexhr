frappe.ui.form.on('Employee', {
    salary_slip_based_on: function (frm) {
        if (frm.doc.salary_slip_based_on == "Attendance") {
            frm.set_df_property("present_based_on", "reqd", 1);
        } else {
            frm.set_df_property("present_based_on", "reqd", 0);
        }
    }
});