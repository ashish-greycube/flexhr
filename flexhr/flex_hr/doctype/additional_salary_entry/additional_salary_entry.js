// Copyright (c) 2018, GreyCube Technologies and contributors
// For license information, please see license.txt

var in_progress = false;

frappe.ui.form.on('Additional Salary Entry', {
	onload: function (frm) {
		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},
	refresh: function(frm) {
		if (frm.doc.docstatus == 0) {
			if(!frm.is_new()) {
				frm.page.clear_primary_action();
				frm.add_custom_button(__("Get Employees"),
					function() {
						frm.events.get_employee_details(frm);
					}
				).toggleClass('btn-primary', !(frm.doc.employees || []).length);
			}
			if ((frm.doc.employees || []).length) {
				frm.page.set_primary_action(__('Create  Additional Salary Slips'), () => {
					frm.save('Submit');
				});
			}
		}
		if (frm.doc.docstatus == 1) {
			if (frm.custom_buttons) frm.clear_custom_buttons();
			frm.events.add_context_buttons(frm);
		}
	},
	get_employee_details: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'fill_employee_details',
			callback: function(r) {
				if (r.docs[0].employees){
					frm.save();
					frm.refresh();

				}
			}
		})
	},
	create_additional_salary_slips: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "create_additional_salary_slips",
			callback: function(r) {
				frm.refresh();
				frm.toolbar.refresh();
			}
		})
	},
	add_context_buttons: function(frm) {
		if(frm.doc.salary_slips_submitted) {
			frm.events.add_bank_entry_button(frm);
		} else if(frm.doc.salary_slips_created) {
			frm.add_custom_button(__("Submit Additional Salary Slip"), function() {
				submit_salary_slip(frm);
			}).addClass("btn-primary");
		}
	},
	company: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	department: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	designation: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	branch: function (frm) {
		frm.events.clear_employee_table(frm);
	},
	set_end_date: function(frm){
		frappe.call({
			method: 'erpnext.hr.doctype.payroll_entry.payroll_entry.get_end_date',
			args: {
				frequency: frm.doc.payroll_frequency,
				start_date: frm.doc.start_date
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value('end_date', r.message.end_date);
				}
			}
		});
	},
	start_date: function (frm) {
		if(!in_progress && frm.doc.start_date){
			if (!frm.doc.payroll_frequency){
				frm.set_value('payroll_frequency', 'Monthly');
			}
			if (frm.doc.payroll_frequency){
				if (frm.doc.payroll_frequency =='Daily'){
				frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 0));

				}
				else if (frm.doc.payroll_frequency =='Weekly'){
					frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 1));

				}
				else{
					frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 5));

				}

			}
			
			frm.trigger("set_end_date");
			// frm.set_value('end_date', frappe.datetime.add_days(frm.doc.start_date, 30));

		}else{
			// reset flag
			in_progress = false;
		}
		frm.events.clear_employee_table(frm);
	},
	clear_employee_table: function (frm) {
		frm.clear_table('employees');
		frm.refresh();
	},
	att_req_btn: function(frm){
		if (frm.doc.start_date == null || frm.doc.end_date == null) {
			frappe.msgprint(__("Set payroll start and end date before checking open attendance request"));
			return false
		}

		if(frm.doc.start_date != null && frm.doc.end_date != null && frm.doc.employees){
			frappe.call({
				method: 'get_open_attendance_request',
				args: {},
				callback: function(r) {
					console.log(r)
					render_attendance_request_html(frm, r.message);
				},
				doc: frm.doc,
				freeze: true,
				freeze_message: 'Finding Open Attendance Request...'
			});
		}else{
			frm.fields_dict.attendance_request_html.html("");
		}
	},
	payroll_frequency: function (frm) {
		if(frm.doc.start_date){
		frm.trigger("set_end_date");
		frm.events.clear_employee_table(frm);
		if (frm.doc.payroll_frequency){
			if (frm.doc.payroll_frequency =='Daily'){
			frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 0));

			}
			else if (frm.doc.payroll_frequency =='Weekly'){
				frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 1));

			}
			else{
				frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 5));

			}

		}
		}
	},
	overtime_app_btn: function(frm){
		if (frm.doc.start_date == null || frm.doc.end_date == null) {
			frappe.msgprint(__("Set payroll start and end date before checking open overtime application"));
			return false
		}

		if(frm.doc.start_date != null && frm.doc.end_date != null && frm.doc.employees){
			frappe.call({
				method: 'get_open_overtime_application',
				args: {},
				callback: function(r) {
					console.log(r)
					render_overtime_application_html(frm, r.message);
				},
				doc: frm.doc,
				freeze: true,
				freeze_message: 'Finding Open Attendance Request...'
			});
		}else{
			frm.fields_dict.overtime_application_html.html("");
		}
	}

});

let render_attendance_request_html = function(frm, data) {
	console.log(data)
	if (data==null) {
		frm.fields_dict.overtime_application_html.html("No matching data found");
	}
	else{
	frm.fields_dict.attendance_request_html.html(
		frappe.render_template('employees_with_open_attendance_request', {
			data: data
		})
	);}
}
let render_overtime_application_html = function(frm, data) {
	console.log(data)
	if (data==null) {
		frm.fields_dict.overtime_application_html.html("No matching data found");
	}
	else{
	frm.fields_dict.overtime_application_html.html(
		frappe.render_template('employees_with_open_overtime_application', {
			data: data
		})
	);
	}
}