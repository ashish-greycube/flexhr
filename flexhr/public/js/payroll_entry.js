var in_progress = false;

frappe.ui.form.on('Payroll Entry', {
	validate_leave: function (frm) {

		if (frm.doc.start_date == null || frm.doc.end_date == null) {
			frappe.msgprint(__("Set payroll start and end date before checking leave details"));
			return false
		}

		if (frm.doc.validate_leave) {
			frappe.call({
				method: 'flexhr.flex_hr.attendance_controller.validate_employee_leave_on_salary_boundary',
				args: {
					'salary_end_date': frm.doc.end_date
				},
				callback: function (r) {
					render_employee_leave(frm, r.message);
				},
				doc: frm.doc,
				freeze: true,
				freeze_message: 'Validating Employee Leave...'
			});
		} else {
			frm.fields_dict.leave_detail_html.html("");
		}
	},
	clickme: function (frm) {
		frappe.call({
			method: "flexhr.flex_hr.attendance_controller.validate_employee_leave_on_salary_boundary",
			args: {
				'salary_end_date': frm.doc.end_date,
				'salary_start_date':frm.doc.start_date
			},
			callback: function (r) {
				render_employee_leave(frm, r.message);
			}
		});
	},
	split_leaves: function (frm) {
		frappe.call({
			method: "flexhr.flex_hr.attendance_controller.split_multiple_leaves",
			args: {
				'salary_end_date': frm.doc.end_date
			},
			callback: function (r) {
				console.log(r)
				// render_employee_leave(frm, r.message);
			}
		});
	},


});
let render_employee_leave = function (frm, data) {
	console.log(frm)
	console.log(data)
	frm.fields_dict.leave_detail_html.html(
		frappe.render_template('employees_with_leaves_on_payroll_boundary', {
			data: data
		})
	);
}