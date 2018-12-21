
frappe.ui.form.on('Payroll Entry', {
	find_leaves: function (frm) {
		if (frm.doc.start_date == null || frm.doc.end_date == null) {
			frappe.msgprint(__("Set payroll start and end date before checking leave details"));
			return false
		}

        var filter = {}

		// var arr_filter=[]
		// filter['status'] = ["=", 'Approved']
		filter['docstatus'] = ["=", '1']
		// filter['from_date'] = ["between", [frm.doc.start_date,frm.doc.end_date]]
		// filter['to_date'] = [">", frm.doc.end_date]
		frappe.route_options = filter
		console.log(filter)
		frappe.set_route("List","Leave Application");
		// frappe.call({
		// 	method: "flexhr.flex_hr.attendance_controller.validate_employee_leave_on_salary_boundary",
		// 	args: {
		// 		'salary_start_date':frm.doc.start_date,
		// 		'salary_end_date': frm.doc.end_date
		// 	},
		// 	callback: function (r) {
		// 		render_employee_leave(frm, r.message);
		// 	}
		// });
	},
	split_leaves: function (frm) {
		frappe.call({
			method: "flexhr.flex_hr.attendance_controller.split_multiple_leaves",
			args: {
				'salary_start_date':frm.doc.start_date,
				'salary_end_date': frm.doc.end_date
			},
			callback: function (r) {
				console.log(r)
				render_employee_leave(frm, r.message);
			}
		});
	},


});
let render_employee_leave = function (frm, data) {
	console.log('data')
	console.log(data)

	if (data==null) {
		frm.fields_dict.leave_detail_html.html("No matching data found");
	}
	else{
	console.log(frm)
	console.log(data)
	frm.fields_dict.leave_detail_html.html(
		frappe.render_template('employees_with_leaves_on_payroll_boundary', {
			data: data
		})
	);}
}