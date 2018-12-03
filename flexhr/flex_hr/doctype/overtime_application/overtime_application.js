// Copyright (c) 2018, GreyCube Technologies and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','employee_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Overtime Application', {
	setup: function(frm) {
		frm.set_query("overtime_approver", function() {
			return {
				query: "erpnext.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype
				}
			};
		}); 

		frm.set_query("employee", erpnext.queries.employee);
	},
	employee: function(frm) {
		frm.trigger("set_overtime_approver");
	},

	overtime_approver: function(frm) {
		if(frm.doc.leave_approver){
			frm.set_value("overtime_approver_name", frappe.user.full_name(frm.doc.overtime_approver));
		}
	},

	set_overtime_approver: function(frm) {
		if(frm.doc.employee) {
				// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'erpnext.hr.doctype.leave_application.leave_application.get_leave_approver',
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('overtime_approver', r.message);
					}
				}
			});
		}
	}
});
