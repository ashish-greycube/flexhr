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
					// frappe.msgprint(r.message);
			  }
			}
		  });
	},
	run_manually:function(frm) {
		if (frm.doc.from_date == null || frm.doc.to_date == null) {
			frappe.msgprint(__("Date cann't be empty"));
			return false
		}
		frm.set_value('last_run_on', '');
		frm.set_value('attendance_log', '');
		return frappe.call({
			method: "call_run_job",
			args: {	},
			callback: function() {frm.events.refresh(frm);},
			doc: frm.doc,
			freeze: true,
			freeze_message: 'Processing Employee checkin data from Attendance Device...'
		  });
	}

});
