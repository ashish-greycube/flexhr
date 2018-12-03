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

	start_date: function (frm) {
		if(!in_progress && frm.doc.start_date){
			frm.set_value('end_date', frappe.datetime.add_days(frm.doc.start_date, 30));
			frm.set_value('posting_date', frappe.datetime.add_days(frm.doc.start_date, 5));
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

});
