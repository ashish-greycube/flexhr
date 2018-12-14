frappe.ui.form.on('Shift Type', {
    is_default: function (frm) {
        if (frm.doc.is_default == 1) {
            frm.set_df_property("late_checkin_deduction_based_on", "reqd", 1);
            frm.set_df_property("early_checkout_deduction_based_on", "reqd", 1);
            frm.set_df_property("min_overtime_required", "reqd", 1);
            frm.set_df_property("max_overtime_allowed", "reqd", 1);
            frm.set_df_property("working_hours", "reqd", 1);

        } else {
            frm.set_df_property("late_checkin_deduction_based_on", "reqd", 0);
            frm.set_df_property("early_checkout_deduction_based_on", "reqd", 0);
            frm.set_df_property("min_overtime_required", "reqd", 0);
            frm.set_df_property("max_overtime_allowed", "reqd", 0);
            frm.set_df_property("working_hours", "reqd", 0);
        }
    },
    late_checkin_deduction_based_on: function (frm) {
        if ((frm.doc.late_checkin_deduction_based_on == 'Late Checkin Deduction Rules') &&
            (frm.doc.is_default == 1)) {
            frm.set_df_property("late_checkin_deduction_rules", "reqd", 1);
        } else {
            frm.set_df_property("late_checkin_deduction_rules", "reqd", 0);
        }
        if ((frm.doc.late_checkin_deduction_based_on == 'Actual Minutes') &&
            (frm.doc.is_default == 1)
        ) {
            frm.set_df_property("ignore_late_in", "reqd", 1);
        } else {
            frm.set_df_property("ignore_late_in", "reqd", 0);
        }
    },
    early_checkout_deduction_based_on: function (frm) {
        if ((frm.doc.early_checkout_deduction_based_on == 'Actual Minutes') &&
            (frm.doc.is_default == 1)) {
            frm.set_df_property("ignore_early_out", "reqd", 1);
        } else {
            frm.set_df_property("ignore_early_out", "reqd", 0);
        }
    },
});