// Copyright (c) 2018, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Processor', {
	refresh: function(frm) {

	},
	run_precheck:function(frm) {
		return frappe.call({
			method: "flexhr.flex_hr.doctype.attendance_processor.attendance_processor.precondition_for_auto_attendance",
			args: {
			},
			callback: function(r) {
			  if (r.message) {
				  alert(r.message);
			  }
			}
		  });
	},
	run_manually:function(frm) {
		return frappe.call({
			method: "flexhr.flex_hr.attendance_controller.run_job",
			args: {
				'start_date': frm.doc.from_date,
				'end_date':frm.doc.to_date
			},
			callback: function(r) {
			  if (r.message) {
				  alert(r.message);
			  }
			}
		  });
	}

});
